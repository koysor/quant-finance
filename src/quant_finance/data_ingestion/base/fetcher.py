"""
Abstract base fetcher class for data ingestion.

Provides the core cache-or-fetch pattern used by all data fetchers.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
import logging
import threading
import pandas as pd

from ..config import DataIngestionConfig, get_default_config
from ..exceptions import (
    CacheError,
    DataIngestionError,
    FetchError,
    RateLimitError,
    SymbolNotFoundError,
    ValidationError,
)
from .cache import BaseCache

logger = logging.getLogger(__name__)

# Bump when the meaning of cached data changes, so older entries are no
# longer read (they expire on their own)
CACHE_KEY_VERSION = "v2"

# One rate limiter per (rate, burst) setting, shared by every fetcher in the
# process. A limiter per fetcher instance would not limit anything, because
# callers such as the Streamlit helpers create a new fetcher for each request.
_shared_limiters: dict[tuple[float, int], Any] = {}
_shared_limiters_lock = threading.Lock()


def _shared_rate_limiter(tokens_per_second: float, bucket_size: int) -> Any:
    """Return the process-wide rate limiter for these settings."""
    from ..utils.rate_limiter import TokenBucketLimiter

    key = (tokens_per_second, bucket_size)
    with _shared_limiters_lock:
        if key not in _shared_limiters:
            _shared_limiters[key] = TokenBucketLimiter(
                tokens_per_second=tokens_per_second, bucket_size=bucket_size
            )
        return _shared_limiters[key]


# Days after a date range ends before its data is treated as final, to allow
# for late corrections from the data source
SETTLEMENT_DAYS = 3


def window_is_closed(end_date: Optional[str]) -> bool:
    """Whether a date range ended long enough ago that its data is final.

    Args:
        end_date: End date in YYYY-MM-DD format, or None for "up to today"

    Returns:
        True if end_date is at least SETTLEMENT_DAYS before today (UTC)
    """
    if not end_date:
        return False
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return False
    return end <= datetime.now(UTC).date() - timedelta(days=SETTLEMENT_DAYS)


def classify_error(error: Exception) -> DataIngestionError:
    """Convert an exception from a data source into a package exception.

    Package exceptions are returned unchanged. Others are matched on their
    message, so that the retry logic can tell errors worth retrying (rate
    limits, server and network errors) from ones that are not (unknown symbol).

    Args:
        error: Exception raised while fetching

    Returns:
        The matching package exception, chained to the original
    """
    if isinstance(error, DataIngestionError):
        return error

    error_msg = str(error).lower()

    converted: DataIngestionError
    if "404" in error_msg or "not found" in error_msg or "no data found" in error_msg:
        converted = SymbolNotFoundError(f"Symbol not found: {error}")
    elif (
        "429" in error_msg
        or "rate limit" in error_msg
        or "too many requests" in error_msg
    ):
        converted = RateLimitError(f"Rate limit exceeded: {error}")
    elif any(code in error_msg for code in ["500", "502", "503", "504"]):
        converted = FetchError(f"Server error: {error}")
    else:
        converted = FetchError(f"Failed to fetch data: {error}")

    converted.__cause__ = error
    return converted


class BaseFetcher(ABC):
    """Abstract base class for all data fetchers.

    Implements the cache-or-fetch pattern with rate limiting,
    retry logic, and data validation.

    Attributes:
        config: Configuration instance
        cache: Cache implementation
        rate_limiter: Rate limiter instance (set in subclasses after utils are imported)
        retry_strategy: Retry strategy instance (set in subclasses after utils are imported)
        cache_table: Name of cache table to use
    """

    def __init__(
        self,
        config: Optional[DataIngestionConfig] = None,
        cache: Optional[BaseCache] = None,
        cache_table: str = "default_cache",
    ):
        """Initialize base fetcher.

        Args:
            config: Configuration instance (uses default if None)
            cache: Cache implementation (uses DuckDB if None)
            cache_table: Name of cache table for this fetcher
        """
        self.config = config or get_default_config()
        self.cache_table = cache_table

        # Cache will be set after importing cache implementations
        self._cache = cache

        # Rate limiter and retry strategy will be set by subclasses
        # after importing utils to avoid circular dependencies
        self._rate_limiter = None
        self._retry_strategy = None

    @property
    def cache(self) -> BaseCache:
        """Get cache instance, lazily initialized."""
        if self._cache is None:
            # Import here to avoid circular dependency
            from ..cache.duckdb_cache import DuckDBCache

            self._cache = DuckDBCache(config=self.config)
        return self._cache

    @property
    def rate_limiter(self):
        """Get the rate limiter shared by all fetchers with the same settings."""
        if self._rate_limiter is None:
            self._rate_limiter = _shared_rate_limiter(
                self.config.rate_limit_per_second, self.config.rate_limit_burst
            )
        return self._rate_limiter

    @property
    def retry_strategy(self):
        """Get retry strategy instance, lazily initialized."""
        if self._retry_strategy is None:
            from ..utils.retry import ExponentialBackoffRetry

            self._retry_strategy = ExponentialBackoffRetry(
                max_retries=self.config.max_retries,
                base_delay=self.config.retry_base_delay,
                max_delay=self.config.retry_max_delay,
            )
        return self._retry_strategy

    @abstractmethod
    def _fetch_impl(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Implementation-specific data fetching logic.

        Subclasses must implement this method to actually fetch data
        from the external source (yfinance, etc.).

        Args:
            **kwargs: Fetcher-specific arguments

        Returns:
            DataFrame with fetched data

        Raises:
            FetchError: If fetching fails
        """
        pass

    @abstractmethod
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate fetched data.

        Subclasses must implement validation logic appropriate
        for their data type.

        Args:
            data: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def _build_cache_key(self, *args: Any, **kwargs: Any) -> str:
        """Build cache key from fetch parameters.

        Subclasses must implement this to create unique,
        deterministic cache keys.

        Args:
            **kwargs: Fetch parameters

        Returns:
            Cache key string
        """
        pass

    def get_cached_or_fetch(self, use_cache: bool = True, **kwargs) -> pd.DataFrame:
        """Get data from cache or fetch if not cached.

        This implements the main cache-or-fetch pattern with
        rate limiting, retry logic, and validation.

        Args:
            use_cache: Whether to use cache (default True)
            **kwargs: Arguments passed to _fetch_impl

        Returns:
            DataFrame with requested data

        Raises:
            FetchError: If fetching fails after retries
            ValidationError: If data validation fails
            CacheError: If cache operations fail critically

        Example:
            >>> fetcher = EquityFetcher()
            >>> df = fetcher.get_cached_or_fetch(
            ...     symbol="AAPL",
            ...     start_date="2023-01-01",
            ...     end_date="2023-12-31"
            ... )
        """
        cache_key = self._build_cache_key(**kwargs)

        # Try cache first if enabled
        if use_cache:
            try:
                cached_data = self.cache.get(cache_key, table=self.cache_table)
                if cached_data is not None:
                    logger.info(f"Cache hit for {cache_key}")
                    return cached_data
                else:
                    logger.debug(f"Cache miss for {cache_key}")
            except CacheError as e:
                logger.warning(f"Cache read failed: {e}, proceeding to fetch")

        data = self._fetch_with_retry(**kwargs)

        # Validate data if enabled
        if self.config.validate_data:
            if not self._validate_data(data):
                raise ValidationError(
                    f"Data validation failed for {cache_key}. "
                    f"Data shape: {data.shape}, columns: {list(data.columns)}"
                )

        # Cache successful fetch
        if use_cache:
            try:
                self.cache.set(
                    cache_key,
                    data,
                    table=self.cache_table,
                    ttl_seconds=self._ttl_seconds(**kwargs),
                    **self._get_cache_metadata(**kwargs),
                )
                logger.info(f"Cached data for {cache_key}")
            except CacheError as e:
                logger.warning(f"Cache write failed: {e}")

        return data

    def _ttl_seconds(self, **kwargs: Any) -> int:
        """How long to cache data fetched with these parameters.

        Subclasses override this when some data changes less often than
        others, for example history over a date range that has ended.

        Args:
            **kwargs: Fetch parameters

        Returns:
            Time-to-live in seconds
        """
        return self.config.default_ttl_seconds

    def _get_cache_metadata(self, *args: Any, **kwargs: Any) -> dict:
        """Get metadata to store with cached data.

        Subclasses can override to add custom metadata.

        Args:
            **kwargs: Fetch parameters

        Returns:
            Dictionary of metadata
        """
        return {}

    def _call_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Call a data-source function with rate limiting and retries.

        Each attempt takes its own rate-limit token, and errors are
        classified before the retry logic sees them, so unknown symbols and
        empty responses fail at once while transient errors are retried.

        Args:
            func: Function that calls the data source
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Whatever func returns

        Raises:
            DataIngestionError: The classified error from the last attempt
        """

        def attempt() -> Any:
            with self.rate_limiter.throttle():
                try:
                    return func(*args, **kwargs)
                except DataIngestionError:
                    raise
                except Exception as e:
                    raise classify_error(e) from e

        return self.retry_strategy.execute(attempt)

    def _fetch_with_retry(self, **kwargs: Any) -> Any:
        """Call _fetch_impl with rate limiting and retries; see _call_with_retry."""
        return self._call_with_retry(self._fetch_impl, **kwargs)

    def invalidate_cache(self, **kwargs) -> None:
        """Invalidate cache for specific parameters.

        Args:
            **kwargs: Fetch parameters to build cache key

        Example:
            >>> fetcher.invalidate_cache(
            ...     symbol="AAPL",
            ...     start_date="2023-01-01",
            ...     end_date="2023-12-31"
            ... )
        """
        cache_key = self._build_cache_key(**kwargs)
        try:
            self.cache.invalidate(cache_key, table=self.cache_table)
            logger.info(f"Invalidated cache for {cache_key}")
        except CacheError as e:
            logger.error(f"Failed to invalidate cache: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(cache_table={self.cache_table})"
