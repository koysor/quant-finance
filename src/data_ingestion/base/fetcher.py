"""
Abstract base fetcher class for data ingestion.

Provides the core cache-or-fetch pattern used by all data fetchers.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging
import pandas as pd

from ..config import DataIngestionConfig, get_default_config
from ..exceptions import FetchError, ValidationError, CacheError
from .cache import BaseCache


logger = logging.getLogger(__name__)


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
    def cache(self) -> Optional[BaseCache]:
        """Get cache instance, lazily initialized."""
        if self._cache is None:
            # Import here to avoid circular dependency
            from ..cache.duckdb_cache import DuckDBCache

            self._cache = DuckDBCache(config=self.config)
        return self._cache

    @property
    def rate_limiter(self):
        """Get rate limiter instance, lazily initialized."""
        if self._rate_limiter is None:
            from ..utils.rate_limiter import TokenBucketLimiter

            self._rate_limiter = TokenBucketLimiter(
                tokens_per_second=self.config.rate_limit_per_second,
                bucket_size=self.config.rate_limit_burst,
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
    def _fetch_impl(self, **kwargs) -> pd.DataFrame:
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
    def _build_cache_key(self, **kwargs) -> str:
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

        # Rate limit check
        with self.rate_limiter.throttle():
            # Fetch with retry
            try:
                data = self.retry_strategy.execute(self._fetch_impl, **kwargs)
            except Exception as e:
                self._handle_fetch_error(e)
                raise

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
                    ttl_seconds=self.config.default_ttl_seconds,
                    **self._get_cache_metadata(**kwargs),
                )
                logger.info(f"Cached data for {cache_key}")
            except CacheError as e:
                logger.warning(f"Cache write failed: {e}")

        return data

    def _get_cache_metadata(self, **kwargs) -> dict:
        """Get metadata to store with cached data.

        Subclasses can override to add custom metadata.

        Args:
            **kwargs: Fetch parameters

        Returns:
            Dictionary of metadata
        """
        return {}

    def _handle_fetch_error(self, error: Exception) -> None:
        """Convert API errors to custom exceptions.

        Args:
            error: Original exception from API

        Raises:
            SymbolNotFoundError: For 404 errors
            RateLimitError: For rate limit errors
            FetchError: For other errors
        """
        from ..exceptions import SymbolNotFoundError, RateLimitError

        error_msg = str(error).lower()

        # Check for symbol not found
        if (
            "404" in error_msg
            or "not found" in error_msg
            or "no data found" in error_msg
        ):
            raise SymbolNotFoundError(f"Symbol not found: {error}") from error

        # Check for rate limit
        if (
            "429" in error_msg
            or "rate limit" in error_msg
            or "too many requests" in error_msg
        ):
            raise RateLimitError(f"Rate limit exceeded: {error}") from error

        # Check for server errors
        if any(code in error_msg for code in ["500", "502", "503", "504"]):
            raise FetchError(f"Server error: {error}") from error

        # Generic fetch error
        raise FetchError(f"Failed to fetch data: {error}") from error

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
