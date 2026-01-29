"""
Equity data fetcher using Yahoo Finance (yfinance).

Provides methods for fetching historical stock prices, OHLCV data,
and stock information.
"""

from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf
import logging

from ..base.fetcher import BaseFetcher
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import FetchError, ValidationError

logger = logging.getLogger(__name__)


class EquityFetcher(BaseFetcher):
    """Fetcher for equity/stock data from Yahoo Finance.

    Supports historical prices, OHLCV data, and stock information
    with automatic caching and rate limiting.

    Example:
        >>> fetcher = EquityFetcher()
        >>> df = fetcher.fetch_historical("AAPL", "2023-01-01", "2023-12-31")
        >>> print(df.head())
    """

    def __init__(self, config: Optional[DataIngestionConfig] = None):
        """Initialize equity fetcher.

        Args:
            config: Configuration instance
        """
        super().__init__(config=config, cache_table="equity_cache")

    def _fetch_impl(
        self, symbol: str, start_date: str, end_date: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch equity data from Yahoo Finance.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, etc.)

        Returns:
            DataFrame with OHLCV data

        Raises:
            FetchError: If fetching fails
        """
        try:
            logger.info(
                f"Fetching {symbol} from {start_date} to {end_date} "
                f"(interval: {interval})"
            )

            # Download data using yfinance
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=self.config.auto_adjust,
                threads=self.config.threads,
                progress=False,
            )

            if df.empty:
                raise FetchError(
                    f"No data returned for {symbol} from {start_date} to {end_date}"
                )

            # Flatten multi-level columns if present (yfinance returns multi-level for single symbols)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            logger.info(f"Fetched {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            raise FetchError(f"Failed to fetch equity data: {e}") from e

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate equity data.

        Args:
            data: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        strict_mode = not self.config.allow_partial_data
        return DataValidator.validate_equity_data(data, strict=strict_mode)

    def _build_cache_key(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        **kwargs,
    ) -> str:
        """Build cache key for equity data.

        Args:
            symbol: Stock ticker
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            Cache key string
        """
        return f"equity:{symbol}:{start_date}:{end_date}:{interval}"

    def _get_cache_metadata(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        **kwargs,
    ) -> dict:
        """Get metadata for caching.

        Args:
            symbol: Stock ticker
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            Metadata dictionary
        """
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
        }

    def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch historical stock data.

        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT', '^GSPC')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('1m', '5m', '1h', '1d', '1wk', '1mo')
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Adj Close

        Raises:
            ValidationError: If date range or symbol is invalid
            FetchError: If fetching fails
            SymbolNotFoundError: If symbol not found

        Example:
            >>> fetcher = EquityFetcher()
            >>> df = fetcher.fetch_historical(
            ...     symbol="AAPL",
            ...     start_date="2023-01-01",
            ...     end_date="2023-12-31",
            ...     interval="1d"
            ... )
            >>> print(df.head())
        """
        # Validate inputs
        if not DataValidator.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol: {symbol}")

        if not DataValidator.validate_date_range(start_date, end_date):
            raise ValidationError(f"Invalid date range: {start_date} to {end_date}")

        if not DataValidator.validate_interval(interval):
            raise ValidationError(f"Invalid interval: {interval}")

        # Fetch using cache-or-fetch pattern
        return self.get_cached_or_fetch(
            use_cache=use_cache,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols.

        Args:
            symbols: List of stock tickers
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval
            use_cache: Whether to use cache

        Returns:
            Dictionary mapping symbols to DataFrames

        Example:
            >>> fetcher = EquityFetcher()
            >>> data = fetcher.fetch_multiple(
            ...     symbols=["AAPL", "MSFT", "GOOGL"],
            ...     start_date="2023-01-01",
            ...     end_date="2023-12-31"
            ... )
            >>> print(data["AAPL"].head())
        """
        result = {}

        for symbol in symbols:
            try:
                df = self.fetch_historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    use_cache=use_cache,
                )
                result[symbol] = df

            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                # Continue with other symbols
                if not self.config.allow_partial_data:
                    raise

        return result

    def fetch_realtime_quote(self, symbol: str) -> Dict[str, any]:
        """Fetch current real-time quote for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Dictionary with current price info

        Example:
            >>> fetcher = EquityFetcher()
            >>> quote = fetcher.fetch_realtime_quote("AAPL")
            >>> print(f"Current price: ${quote['price']:.2f}")
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
            }

        except Exception as e:
            logger.error(f"Failed to fetch quote for {symbol}: {e}")
            raise FetchError(f"Failed to fetch real-time quote: {e}") from e

    def get_info(self, symbol: str) -> Dict[str, any]:
        """Get detailed information about a stock.

        Args:
            symbol: Stock ticker

        Returns:
            Dictionary with stock information

        Example:
            >>> fetcher = EquityFetcher()
            >>> info = fetcher.get_info("AAPL")
            >>> print(f"Company: {info['longName']}")
            >>> print(f"Sector: {info['sector']}")
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info

        except Exception as e:
            logger.error(f"Failed to fetch info for {symbol}: {e}")
            raise FetchError(f"Failed to fetch stock info: {e}") from e
