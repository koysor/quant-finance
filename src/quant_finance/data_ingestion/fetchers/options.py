"""
Options data fetcher using Yahoo Finance (yfinance).

Provides methods for fetching options chains and available expirations.
"""

import warnings
from typing import Any, List, Optional, Tuple
import pandas as pd
import yfinance as yf
import logging

from ..base.fetcher import CACHE_KEY_VERSION, BaseFetcher
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import NoDataError, ValidationError

logger = logging.getLogger(__name__)

# Columns added to the combined chain that is cached
OPTION_TYPE_COLUMN = "OptionType"
EXPIRATION_COLUMN = "Expiration"


def _split_chain(chain: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split a combined chain into (calls, puts), dropping the type column."""
    sides = []
    for option_type in ("call", "put"):
        side = chain[chain[OPTION_TYPE_COLUMN] == option_type]
        sides.append(side.drop(columns=OPTION_TYPE_COLUMN).reset_index(drop=True))
    return sides[0], sides[1]


class OptionsFetcher(BaseFetcher):
    """Fetcher for options data from Yahoo Finance.

    Supports options chains and expirations with automatic caching and rate
    limiting. Greeks are not provided by Yahoo Finance; compute them with
    quant_finance.pricing.black_scholes from the chain's implied volatilities.

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
    ) -> pd.DataFrame:
        """Fetch an options chain from Yahoo Finance.

        Args:
            symbol: Stock ticker symbol
            expiration: Expiration date (YYYY-MM-DD) or None for nearest

        Returns:
            Calls and puts in one DataFrame, with an OptionType column ("call"
            or "put") and an Expiration column holding the expiry fetched

        Raises:
            NoDataError: If the symbol has no options or the chain is empty

        Errors from yfinance are left to the base class to classify.
        """
        logger.info(f"Fetching options chain for {symbol} exp: {expiration}")

        ticker = yf.Ticker(symbol)

        if not expiration:
            # Use nearest expiration
            expirations = ticker.options
            if not expirations:
                raise NoDataError(f"No options available for {symbol}")
            expiration = expirations[0]
        opt_chain = ticker.option_chain(expiration)

        calls = opt_chain.calls
        puts = opt_chain.puts

        if calls.empty and puts.empty:
            raise NoDataError(
                f"No options data returned for {symbol} exp: {expiration}"
            )

        # Rename columns to standardized format
        column_mapping = {
            "strike": "Strike",
            "lastPrice": "Last",
            "bid": "Bid",
            "ask": "Ask",
            "volume": "Volume",
            "openInterest": "OpenInterest",
            "impliedVolatility": "ImpliedVolatility",
        }

        logger.info(
            f"Fetched options for {symbol}: {len(calls)} calls, {len(puts)} puts"
        )

        chain = pd.concat(
            [
                calls.rename(columns=column_mapping).assign(
                    **{OPTION_TYPE_COLUMN: "call"}
                ),
                puts.rename(columns=column_mapping).assign(
                    **{OPTION_TYPE_COLUMN: "put"}
                ),
            ],
            ignore_index=True,
        )
        chain[EXPIRATION_COLUMN] = expiration
        return chain

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate options data.

        Args:
            data: Combined chain from _fetch_impl

        Returns:
            True if valid, False otherwise
        """
        if OPTION_TYPE_COLUMN not in data.columns:
            logger.error(f"Options data has no {OPTION_TYPE_COLUMN} column")
            return False

        calls, puts = _split_chain(data)
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
        return f"options:{CACHE_KEY_VERSION}:{symbol}:{exp_str}"

    def _get_cache_metadata(
        self, symbol: str, expiration: Optional[str] = None, **kwargs
    ) -> dict:
        """Get metadata for caching.

        For the nearest expiry the date is not known until the chain is
        fetched; it is stored in the chain's Expiration column instead.

        Args:
            symbol: Stock ticker
            expiration: Expiration date requested, or None for nearest

        Returns:
            Metadata dictionary
        """
        return {"symbol": symbol, "expiration": expiration}

    def _ttl_seconds(self, **kwargs: Any) -> int:
        """Option prices move intraday, so chains are cached briefly."""
        return self.config.options_ttl_seconds

    def get_available_expirations(self, symbol: str) -> List[str]:
        """Get list of available expiration dates for a symbol.

        Not cached, but rate limited and retried.

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
        expirations = self._call_with_retry(lambda: yf.Ticker(symbol).options)

        if not expirations:
            logger.warning(f"No options expirations found for {symbol}")
            return []

        logger.info(f"Found {len(expirations)} expirations for {symbol}")
        return list(expirations)

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
            OpenInterest, ImpliedVolatility and Expiration (the expiry
            fetched, which matters when expiration is None)

        Raises:
            ValidationError: If symbol is invalid
            NoDataError: If there is no chain for the symbol and expiry
            FetchError: If fetching fails

        Example:
            >>> fetcher = OptionsFetcher()
            >>> calls, puts = fetcher.fetch_option_chain("AAPL", "2024-01-19")
            >>> print(calls[['Strike', 'Last', 'ImpliedVolatility']].head())
        """
        if not DataValidator.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol: {symbol}")

        chain = self.get_cached_or_fetch(
            use_cache=use_cache, symbol=symbol, expiration=expiration
        )
        return _split_chain(chain)

    def fetch_greeks(
        self, symbol: str, expiration: str, option_type: str = "call"
    ) -> pd.DataFrame:
        """Fetch one side of an options chain.

        Deprecated: despite its name this computes no Greeks; it returns the
        calls or the puts from fetch_option_chain, whose ImpliedVolatility
        column can be passed to the Greeks in quant_finance.pricing.black_scholes.

        Args:
            symbol: Stock ticker
            expiration: Expiration date
            option_type: 'call' or 'put'

        Returns:
            The calls or puts DataFrame
        """
        warnings.warn(
            "fetch_greeks computes no Greeks and is deprecated; use "
            "fetch_option_chain and quant_finance.pricing.black_scholes",
            DeprecationWarning,
            stacklevel=2,
        )
        if option_type.lower() not in ("call", "put"):
            raise ValidationError(
                f"Invalid option_type: {option_type}. Must be 'call' or 'put'"
            )
        calls, puts = self.fetch_option_chain(symbol, expiration)
        return calls if option_type.lower() == "call" else puts

    def __repr__(self) -> str:
        """String representation."""
        return f"OptionsFetcher(cache_table={self.cache_table})"
