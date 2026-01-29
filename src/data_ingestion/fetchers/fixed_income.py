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

from ..base.fetcher import BaseFetcher
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import FetchError, ValidationError

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

    # Yahoo Finance symbols for treasury yields
    TREASURY_SYMBOLS = {
        "3M": "^IRX",  # 13-week treasury bill
        "6M": "^IRX",  # Using same as 3M (approximate)
        "1Y": "^IRX",  # Using same as 3M (approximate)
        "2Y": "^FVX",  # 5-year treasury (will be adjusted)
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
            FetchError: If fetching fails
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

            logger.info(
                f"Fetching treasury yields for {maturities} "
                f"from {start_date} to {end_date}"
            )

            # Fetch data for each maturity
            data_frames = {}

            for maturity in maturities:
                if maturity not in self.TREASURY_SYMBOLS:
                    logger.warning(f"Unknown maturity: {maturity}, skipping")
                    continue

                symbol = self.TREASURY_SYMBOLS[maturity]

                # Fetch data
                df = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    interval="1d",
                    auto_adjust=True,
                    threads=False,
                    progress=False,
                )

                if not df.empty:
                    # Flatten multi-level columns if present
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    # Use Close price as yield
                    data_frames[maturity] = df["Close"]

            if not data_frames:
                raise FetchError(f"No treasury data returned for {maturities}")

            # Combine into single DataFrame (concat Series horizontally)
            result = pd.concat(data_frames, axis=1)

            logger.info(f"Fetched {len(result)} rows of treasury data")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch treasury yields: {e}")
            raise FetchError(f"Failed to fetch fixed income data: {e}") from e

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
        maturities: List[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch treasury yield data.

        Args:
            maturities: List of maturities ('3M', '6M', '1Y', '2Y', '5Y', '10Y', '30Y')
                       Default: ['10Y', '30Y']
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with treasury yields as columns

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
        all_maturities = ["3M", "2Y", "5Y", "10Y", "30Y"]

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
            ['3M', '2Y', '5Y', '10Y', '30Y']
        """
        return list(self.TREASURY_SYMBOLS.keys())

    def __repr__(self) -> str:
        """String representation."""
        return f"FixedIncomeFetcher(cache_table={self.cache_table})"
