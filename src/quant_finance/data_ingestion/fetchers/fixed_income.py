"""
Fixed income data fetcher for US Treasury par yields (from FRED).

Provides methods for fetching treasury yields and yield curves, adding the
package's caching, rate limiting and retries to ``quant_finance.rates.treasury``.
"""

from typing import List, Optional
import pandas as pd
import logging
from datetime import datetime, timedelta

from ..base.fetcher import BaseFetcher, window_is_closed
from ..config import DataIngestionConfig
from ..utils.validators import DataValidator
from ..exceptions import NoDataError, ValidationError
from ...rates import treasury

logger = logging.getLogger(__name__)


class FixedIncomeFetcher(BaseFetcher):
    """Fetcher for US Treasury par yields from FRED.

    The yields are the Federal Reserve's constant-maturity Treasury (CMT)
    series, in percent and all on the same bond-equivalent basis, so every
    tenor from 1M to 30Y is directly comparable. Fetches are cached, rate
    limited and retried.

    Example:
        >>> fetcher = FixedIncomeFetcher()
        >>> yields_df = fetcher.fetch_treasury_yields(
        ...     maturities=["2Y", "10Y"],
        ...     start_date="2023-01-01",
        ...     end_date="2023-12-31"
        ... )
    """

    # FRED series for each tenor (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
    TREASURY_SERIES = treasury.TREASURY_SERIES

    def __init__(self, config: Optional[DataIngestionConfig] = None):
        """Initialise fixed income fetcher.

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
        """Fetch treasury par yields from FRED.

        Args:
            maturities: List of maturities (e.g., ['3M', '10Y', '30Y'])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), included

        Returns:
            DataFrame with one column of yields in percent per maturity

        Raises:
            ValidationError: If a maturity is not supported
            NoDataError: If FRED returns no data for the range

        Errors from the download are left to the base class to classify (an
        unknown series is an HTTP 404, which becomes SymbolNotFoundError).
        """
        _check_maturities(maturities)

        logger.info(
            f"Fetching treasury yields for {maturities} from {start_date} to {end_date}"
        )
        result = treasury.fetch_treasury_par_yields(maturities, start_date, end_date)
        if result.dropna(how="all").empty:
            raise NoDataError(
                f"No treasury data returned for {maturities} "
                f"from {start_date} to {end_date}"
            )

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

        The key names the source, so entries cached from Yahoo Finance before
        the switch to FRED are never read back.

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
        return f"fixedincome:fred:{maturities_str}:{start_str}:{end_str}"

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
        """Fetch treasury par yield data.

        Args:
            maturities: Tenors from get_available_maturities()
                       Default: ['10Y', '30Y']
            start_date: Start date in YYYY-MM-DD format (default: 1 year
                before the end date)
            end_date: End date in YYYY-MM-DD format, included (default: today)
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with treasury yields in percent as columns, shortest
            tenor first

        Raises:
            ValidationError: If a maturity is not supported or the dates are invalid

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> yields = fetcher.fetch_treasury_yields(
            ...     maturities=["2Y", "10Y"],
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
        """Fetch the yield curve for a specific date.

        On a weekend or holiday the curve is the one from the previous
        business day.

        Args:
            date: Date in YYYY-MM-DD format (default: today)
            use_cache: Whether to use cache

        Returns:
            DataFrame with columns Maturity (e.g. "2Y"), Years (2.0) and
            Yield (percent), shortest maturity first

        Raises:
            NoDataError: If there are no yields in the 10 days up to the date

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> curve = fetcher.fetch_yield_curve("2023-12-29")
            >>> print(curve)
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Fetch a short range ending on the target date, long enough to span
        # a holiday weekend
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start = (target_date - timedelta(days=10)).strftime("%Y-%m-%d")

        df = self.fetch_treasury_yields(
            maturities=self.get_available_maturities(),
            start_date=start,
            end_date=date,
            use_cache=use_cache,
        )

        try:
            yields = treasury.curve_on(df, date)
        except ValueError as error:
            raise NoDataError(str(error)) from error

        return pd.DataFrame(
            {
                "Maturity": yields.index,
                "Years": [treasury.TENOR_YEARS[m] for m in yields.index],
                "Yield": yields.values,
            }
        )

    def get_available_maturities(self) -> List[str]:
        """Get list of available treasury maturities, shortest first.

        Returns:
            List of maturity strings

        Example:
            >>> fetcher = FixedIncomeFetcher()
            >>> fetcher.get_available_maturities()
            ['1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
        """
        return list(self.TREASURY_SERIES.keys())

    def __repr__(self) -> str:
        """String representation."""
        return f"FixedIncomeFetcher(cache_table={self.cache_table})"


def _check_maturities(maturities: List[str]) -> None:
    """Raise ValidationError if any maturity has no data source."""
    try:
        treasury.check_maturities(maturities)
    except ValueError as error:
        raise ValidationError(str(error)) from error
