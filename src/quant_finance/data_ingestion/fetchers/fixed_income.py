"""
Fixed income data fetcher using Yahoo Finance (yfinance).

Provides methods for fetching treasury yields, yield curves,
and bond-related data.
"""

from typing import List, Optional
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta

from ..base.fetcher import BaseFetcher, window_is_closed
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import NoDataError, ValidationError

logger = logging.getLogger(__name__)


class FixedIncomeFetcher(BaseFetcher):
    """Fetcher for fixed income data from Yahoo Finance.

    Supports treasury yields, yield curves, and bond indices
    with automatic caching and rate limiting.

    Example:
        >>> fetcher = FixedIncomeFetcher()
        >>> yields_df = fetcher.fetch_treasury_yields(
        ...     maturities=["10Y", "30Y"],
        ...     start_date="2023-01-01",
        ...     end_date="2023-12-31"
        ... )
    """

    # Yahoo Finance symbols for treasury yields. Only tenors with their own
    # index are listed: mapping a tenor to another tenor's series (as 2Y to
    # the 5-year index) would put wrong numbers under the right label.
    # Values are quoted in percent (4.25 means 4.25%). ^IRX is the 13-week
    # bill rate on a discount basis; the others are bond-equivalent yields.
    TREASURY_SYMBOLS = {
        "3M": "^IRX",  # 13-week treasury bill
        "5Y": "^FVX",  # 5-year treasury yield
        "10Y": "^TNX",  # 10-year treasury yield
        "30Y": "^TYX",  # 30-year treasury yield
    }

    def __init__(self, config: Optional[DataIngestionConfig] = None):
        """Initialize fixed income fetcher.

        Args:
            config: Configuration instance
        """
        super().__init__(config=config, cache_table="fixed_income_cache")

    def _fetch_impl(
        self,
        maturities: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch treasury yield data from Yahoo Finance.

        Args:
            maturities: List of maturities (e.g., ['3M', '10Y', '30Y'])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with treasury yields

        Raises:
            ValidationError: If a maturity is not supported
            NoDataError: If no data is returned for any maturity

        Errors from yfinance are left to the base class to classify.
        """
        _check_maturities(maturities)

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        logger.info(
            f"Fetching treasury yields for {maturities} from {start_date} to {end_date}"
        )

        # Fetch data for each maturity
        data_frames = {}

        for maturity in maturities:
            symbol = self.TREASURY_SYMBOLS[maturity]

            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval="1d",
                auto_adjust=True,
                threads=False,
                progress=False,
            )

            if df is None or df.empty:
                logger.warning(f"No data returned for {maturity} ({symbol})")
                continue

            # Flatten multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Use Close price as yield
            data_frames[maturity] = df["Close"]

        if not data_frames:
            raise NoDataError(f"No treasury data returned for {maturities}")

        # Combine into single DataFrame (concat Series horizontally)
        result = pd.concat(data_frames, axis=1)

        logger.info(f"Fetched {len(result)} rows of treasury data")
        return result

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate fixed income data.

        Args:
            data: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        strict_mode = not self.config.allow_partial_data
        return DataValidator.validate_fixed_income_data(data, strict=strict_mode)

    def _build_cache_key(
        self,
        maturities: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Build cache key for fixed income data.

        Args:
            maturities: List of maturities
            start_date: Start date
            end_date: End date

        Returns:
            Cache key string
        """
        maturities_str = ",".join(sorted(maturities))
        start_str = start_date or "default"
        end_str = end_date or "default"
        return f"fixedincome:{maturities_str}:{start_str}:{end_str}"

    def _ttl_seconds(self, end_date: Optional[str] = None, **kwargs) -> int:
        """Cache yields over a date range that has ended for longer.

        Yields are not adjusted after the fact, so once a range has ended its
        data is final. With no end date the range runs to today.
        """
        if window_is_closed(end_date):
            return self.config.closed_window_ttl_seconds
        return self.config.default_ttl_seconds

    def _get_cache_metadata(
        self,
        maturities: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Get metadata for caching.

        Args:
            maturities: List of maturities
            start_date: Start date
            end_date: End date

        Returns:
            Metadata dictionary
        """
        return {
            "instrument": "treasury",
            "maturity": ",".join(maturities),
            "start_date": start_date,
            "end_date": end_date,
        }

    def fetch_treasury_yields(
        self,
        maturities: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch treasury yield data.

        Args:
            maturities: List of maturities ('3M', '5Y', '10Y', '30Y')
                       Default: ['10Y', '30Y']
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with treasury yields in percent as columns

        Raises:
            ValidationError: If a maturity is not supported or the dates are invalid

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> yields = fetcher.fetch_treasury_yields(
            ...     maturities=["10Y", "30Y"],
            ...     start_date="2023-01-01",
            ...     end_date="2023-12-31"
            ... )
            >>> print(yields.head())
        """
        # Default maturities
        if maturities is None:
            maturities = ["10Y", "30Y"]

        # Reject unsupported tenors before fetching, rather than skipping them
        _check_maturities(maturities)

        # Validate date range if provided
        if start_date and end_date:
            if not DataValidator.validate_date_range(start_date, end_date):
                raise ValidationError(f"Invalid date range: {start_date} to {end_date}")

        # Fetch using cache-or-fetch pattern
        return self.get_cached_or_fetch(
            use_cache=use_cache,
            maturities=maturities,
            start_date=start_date,
            end_date=end_date,
        )

    def fetch_yield_curve(
        self, date: Optional[str] = None, use_cache: bool = True
    ) -> pd.DataFrame:
        """Fetch yield curve for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (default: today)
            use_cache: Whether to use cache

        Returns:
            DataFrame with maturity vs yield

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> curve = fetcher.fetch_yield_curve("2023-12-31")
            >>> print(curve)
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Fetch all maturities for the date
        all_maturities = self.get_available_maturities()

        # Get a small date range around the target date
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start = (target_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

        df = self.fetch_treasury_yields(
            maturities=all_maturities,
            start_date=start,
            end_date=end,
            use_cache=use_cache,
        )

        # Get the row closest to the target date
        if date in df.index:
            yields = df.loc[date]
        else:
            # Find nearest date
            yields = df.iloc[-1]

        # Convert to DataFrame with maturity and yield columns
        result = pd.DataFrame({"Maturity": yields.index, "Yield": yields.values})

        return result

    def get_available_maturities(self) -> List[str]:
        """Get list of available treasury maturities.

        Returns:
            List of maturity strings

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> maturities = fetcher.get_available_maturities()
            >>> print(maturities)
            ['3M', '5Y', '10Y', '30Y']
        """
        return list(self.TREASURY_SYMBOLS.keys())


def _check_maturities(maturities: List[str]) -> None:
    """Raise ValidationError if any maturity has no data source."""
    unknown = [m for m in maturities if m not in FixedIncomeFetcher.TREASURY_SYMBOLS]
    if unknown:
        raise ValidationError(
            f"Unsupported maturities {unknown}; available: "
            f"{list(FixedIncomeFetcher.TREASURY_SYMBOLS)}"
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"FixedIncomeFetcher(cache_table={self.cache_table})"
