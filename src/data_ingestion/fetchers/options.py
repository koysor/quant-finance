"""
Options data fetcher using Yahoo Finance (yfinance).

Provides methods for fetching options chains, available expirations,
and options data with Greeks.
"""

from typing import List, Optional, Tuple
import pandas as pd
import yfinance as yf
import logging

from ..base.fetcher import BaseFetcher
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import FetchError, ValidationError


logger = logging.getLogger(__name__)


class OptionsFetcher(BaseFetcher):
    """Fetcher for options data from Yahoo Finance.

    Supports options chains, expirations, and calculated Greeks
    with automatic caching and rate limiting.

    Example:
        >>> fetcher = OptionsFetcher()
        >>> calls, puts = fetcher.fetch_option_chain("AAPL", "2024-01-19")
    """

    def __init__(self, config: Optional[DataIngestionConfig] = None):
        """Initialize options fetcher.

        Args:
            config: Configuration instance
        """
        super().__init__(config=config, cache_table="options_cache")

    def _fetch_impl(
        self, symbol: str, expiration: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch options chain from Yahoo Finance.

        Args:
            symbol: Stock ticker symbol
            expiration: Expiration date (YYYY-MM-DD) or None for nearest

        Returns:
            Tuple of (calls DataFrame, puts DataFrame)

        Raises:
            FetchError: If fetching fails
        """
        try:
            logger.info(f"Fetching options chain for {symbol} exp: {expiration}")

            # Get ticker object
            ticker = yf.Ticker(symbol)

            # Get options chain for specified expiration
            if expiration:
                opt_chain = ticker.option_chain(expiration)
            else:
                # Use nearest expiration
                expirations = ticker.options
                if not expirations:
                    raise FetchError(f"No options available for {symbol}")
                expiration = expirations[0]
                opt_chain = ticker.option_chain(expiration)

            calls = opt_chain.calls
            puts = opt_chain.puts

            if calls.empty and puts.empty:
                raise FetchError(
                    f"No options data returned for {symbol} exp: {expiration}"
                )

            # Rename columns to standardized format
            column_mapping = {
                "strike": "Strike",
                "lastPrice": "Last",
                "volume": "Volume",
                "openInterest": "OpenInterest",
                "impliedVolatility": "ImpliedVolatility",
            }

            calls = calls.rename(columns=column_mapping)
            puts = puts.rename(columns=column_mapping)

            logger.info(
                f"Fetched options for {symbol}: {len(calls)} calls, {len(puts)} puts"
            )

            # Store expiration for metadata
            self._last_expiration = expiration

            return calls, puts

        except Exception as e:
            logger.error(f"Failed to fetch options for {symbol}: {e}")
            raise FetchError(f"Failed to fetch options data: {e}") from e

    def _validate_data(self, data: any) -> bool:
        """Validate options data.

        Args:
            data: Tuple of (calls, puts) DataFrames

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, tuple) or len(data) != 2:
            logger.error("Options data must be tuple of (calls, puts)")
            return False

        calls, puts = data
        strict_mode = not self.config.allow_partial_data

        return DataValidator.validate_options_data(calls, puts, strict=strict_mode)

    def _build_cache_key(
        self, symbol: str, expiration: Optional[str] = None, **kwargs
    ) -> str:
        """Build cache key for options data.

        Args:
            symbol: Stock ticker
            expiration: Expiration date

        Returns:
            Cache key string
        """
        exp_str = expiration if expiration else "nearest"
        return f"options:{symbol}:{exp_str}"

    def _get_cache_metadata(
        self, symbol: str, expiration: Optional[str] = None, **kwargs
    ) -> dict:
        """Get metadata for caching.

        Args:
            symbol: Stock ticker
            expiration: Expiration date

        Returns:
            Metadata dictionary
        """
        # Use the expiration that was actually fetched
        actual_expiration = getattr(self, "_last_expiration", expiration)

        return {"symbol": symbol, "expiration": actual_expiration}

    def get_available_expirations(self, symbol: str) -> List[str]:
        """Get list of available expiration dates for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            List of expiration dates in YYYY-MM-DD format

        Example:
            >>> fetcher = OptionsFetcher()
            >>> expirations = fetcher.get_available_expirations("AAPL")
            >>> print(expirations)
            ['2024-01-19', '2024-01-26', '2024-02-16', ...]
        """
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options

            if not expirations:
                logger.warning(f"No options expirations found for {symbol}")
                return []

            logger.info(f"Found {len(expirations)} expirations for {symbol}")
            return list(expirations)

        except Exception as e:
            logger.error(f"Failed to get expirations for {symbol}: {e}")
            raise FetchError(f"Failed to get available expirations: {e}") from e

    def fetch_option_chain(
        self, symbol: str, expiration: Optional[str] = None, use_cache: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch options chain for a symbol.

        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
            expiration: Expiration date in YYYY-MM-DD format (None for nearest)
            use_cache: Whether to use cached data if available

        Returns:
            Tuple of (calls DataFrame, puts DataFrame)
            Each DataFrame contains: Strike, Last, Bid, Ask, Volume,
            OpenInterest, ImpliedVolatility

        Raises:
            ValidationError: If symbol is invalid
            FetchError: If fetching fails
            SymbolNotFoundError: If symbol not found

        Example:
            >>> fetcher = OptionsFetcher()
            >>> calls, puts = fetcher.fetch_option_chain("AAPL", "2024-01-19")
            >>> print(calls[['Strike', 'Last', 'ImpliedVolatility']].head())
        """
        # Validate symbol
        if not DataValidator.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol: {symbol}")

        # Fetch using cache-or-fetch pattern
        # Note: The base class get_cached_or_fetch expects a single DataFrame
        # but we return a tuple, so we need special handling

        cache_key = self._build_cache_key(symbol=symbol, expiration=expiration)

        # Try cache first if enabled
        if use_cache:
            try:
                cached_data = self.cache.get(cache_key, table=self.cache_table)
                if cached_data is not None:
                    # Cached data is pickled tuple
                    logger.info(f"Cache hit for {cache_key}")
                    return cached_data
            except Exception as e:
                logger.warning(f"Cache read failed: {e}, proceeding to fetch")

        # Fetch with rate limiting
        with self.rate_limiter.throttle():
            try:
                data = self.retry_strategy.execute(
                    self._fetch_impl, symbol=symbol, expiration=expiration
                )
            except Exception as e:
                self._handle_fetch_error(e)
                raise

        # Validate
        if self.config.validate_data:
            if not self._validate_data(data):
                raise ValidationError(f"Options data validation failed for {cache_key}")

        # Cache the tuple
        if use_cache:
            try:
                # Note: DuckDB cache stores DataFrames, but we can pickle the tuple
                # We'll store it as a single pickled object
                self.cache.set(
                    cache_key,
                    data,  # This is the tuple (calls, puts)
                    table=self.cache_table,
                    ttl_seconds=1800,  # 30 minutes for options
                    **self._get_cache_metadata(symbol=symbol, expiration=expiration),
                )
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")

        return data

    def fetch_greeks(
        self, symbol: str, expiration: str, option_type: str = "call"
    ) -> pd.DataFrame:
        """Fetch options chain with calculated Greeks.

        Note: yfinance provides implied volatility but not all Greeks.
        For full Greeks calculation, consider using scipy or dedicated libraries.

        Args:
            symbol: Stock ticker
            expiration: Expiration date
            option_type: 'call' or 'put'

        Returns:
            DataFrame with options data including available Greeks

        Example:
            >>> fetcher = OptionsFetcher()
            >>> greeks_df = fetcher.fetch_greeks("AAPL", "2024-01-19", "call")
            >>> print(greeks_df[['Strike', 'ImpliedVolatility']].head())
        """
        calls, puts = self.fetch_option_chain(symbol, expiration)

        if option_type.lower() == "call":
            return calls
        elif option_type.lower() == "put":
            return puts
        else:
            raise ValidationError(
                f"Invalid option_type: {option_type}. Must be 'call' or 'put'"
            )

    def __repr__(self) -> str:
        """String representation."""
        return f"OptionsFetcher(cache_table={self.cache_table})"
