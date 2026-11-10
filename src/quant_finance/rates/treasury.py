"""US Treasury par yields from FRED, and yield curve helpers.

The series are the Federal Reserve's H.15 constant-maturity Treasury (CMT)
yields, published on FRED as ``DGS1MO`` ... ``DGS30``. A CMT yield is the
par yield of a notional Treasury with exactly that maturity, interpolated by
the US Treasury from on-the-run securities. Every tenor, bills included, is
quoted on the same investment (bond-equivalent) basis, in percent: 4.25 means
4.25% a year. That makes the tenors directly comparable, unlike Yahoo
Finance's ``^IRX``, which is a bill rate on a discount basis.

This module uses only the standard library and pandas, so the Streamlit apps
can use it without loading DuckDB or yfinance. ``FixedIncomeFetcher`` in
``quant_finance.data_ingestion`` adds caching, rate limiting and retries on
top of it.
"""

import io
import urllib.parse
import urllib.request
from collections.abc import Sequence
from datetime import date

import pandas as pd

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# FRED series for each tenor, shortest first
TREASURY_SERIES: dict[str, str] = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

# Tenor in years, for plotting a curve against maturity
TENOR_YEARS: dict[str, float] = {
    "1M": 1 / 12,
    "3M": 0.25,
    "6M": 0.5,
    "1Y": 1.0,
    "2Y": 2.0,
    "3Y": 3.0,
    "5Y": 5.0,
    "7Y": 7.0,
    "10Y": 10.0,
    "20Y": 20.0,
    "30Y": 30.0,
}

type DateLike = str | date | pd.Timestamp


def check_maturities(maturities: Sequence[str]) -> None:
    """Raise ValueError if any maturity is not a tenor in TREASURY_SERIES."""
    unknown = [m for m in maturities if m not in TREASURY_SERIES]
    if unknown:
        raise ValueError(
            f"Unsupported maturities {unknown}; available: {list(TREASURY_SERIES)}"
        )


def fred_csv_url(series_ids: Sequence[str], start: DateLike, end: DateLike) -> str:
    """URL of FRED's CSV download for several series over a date range.

    FRED applies a date range only to the series in the matching position, so
    the start and end dates are repeated once per series. A single start and
    end with several series returns each series' full history.
    """
    if not series_ids:
        raise ValueError("At least one series is needed")
    start_str = pd.Timestamp(start).strftime("%Y-%m-%d")
    end_str = pd.Timestamp(end).strftime("%Y-%m-%d")
    query = urllib.parse.urlencode(
        {
            "id": ",".join(series_ids),
            "cosd": ",".join([start_str] * len(series_ids)),
            "coed": ",".join([end_str] * len(series_ids)),
        },
        safe=",",
    )
    return f"{FRED_CSV_URL}?{query}"


def parse_fred_csv(text: str) -> pd.DataFrame:
    """Parse FRED's CSV download into a float frame indexed by date.

    Missing values (empty, or "." in older downloads) become NaN, and dates
    on which every series is missing (market holidays) are dropped.
    """
    frame = pd.read_csv(
        io.StringIO(text), index_col=0, parse_dates=True, na_values=["."]
    )
    frame.index.name = "Date"
    return frame.astype(float).dropna(how="all")


def fetch_fred_series(
    series_ids: Sequence[str],
    start: DateLike,
    end: DateLike,
    timeout: float = 30.0,
) -> pd.DataFrame:
    """Download FRED series over a date range (both dates included).

    No API key is needed for the CSV download. Errors are not caught: an
    unknown series raises ``urllib.error.HTTPError`` (404), and a network
    failure raises ``urllib.error.URLError``.

    Returns:
        One float column per series, named by series ID, indexed by date
    """
    request = urllib.request.Request(
        fred_csv_url(series_ids, start, end),
        headers={"User-Agent": "quant-finance/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        text = response.read().decode("utf-8")
    return parse_fred_csv(text)


def fetch_treasury_par_yields(
    maturities: Sequence[str] | None = None,
    start: DateLike | None = None,
    end: DateLike | None = None,
    timeout: float = 30.0,
) -> pd.DataFrame:
    """Daily Treasury par yields in percent, one column per tenor.

    Args:
        maturities: Tenors from TREASURY_SERIES (default: all of them)
        start: First date (default: one year before ``end``)
        end: Last date, included (default: today)
        timeout: Seconds to wait for FRED

    Returns:
        Columns named by tenor (e.g. "2Y"), shortest first, indexed by date.
        A tenor is NaN on dates before its series began (1M starts in 2001,
        20Y has a gap from 1987 to 1993).
    """
    if maturities is None:
        maturities = list(TREASURY_SERIES)
    check_maturities(maturities)
    end_ts = pd.Timestamp(end) if end is not None else pd.Timestamp.today().normalize()
    start_ts = (
        pd.Timestamp(start) if start is not None else end_ts - pd.DateOffset(years=1)
    )

    ordered = [m for m in TREASURY_SERIES if m in maturities]
    frame = fetch_fred_series(
        [TREASURY_SERIES[m] for m in ordered], start_ts, end_ts, timeout=timeout
    )
    by_series = {series: tenor for tenor, series in TREASURY_SERIES.items()}
    return frame.rename(columns=by_series).reindex(columns=ordered)


def curve_on(yields: pd.DataFrame, on: DateLike) -> pd.Series:
    """The curve on the last date with data on or before ``on``.

    Args:
        yields: Par yields as returned by fetch_treasury_par_yields
        on: Date of the curve; weekends and holidays use the previous
            business day

    Returns:
        Yields indexed by tenor, without tenors that have no value that day.
        The series is named by the date actually used.

    Raises:
        ValueError: If there is no data on or before ``on``
    """
    available = yields.loc[: pd.Timestamp(on)].dropna(how="all")
    if available.empty:
        raise ValueError(f"No yields on or before {pd.Timestamp(on).date()}")
    return available.iloc[-1].dropna()


def yield_spread(
    yields: pd.DataFrame, long: str = "10Y", short: str = "2Y"
) -> pd.Series:
    """Long minus short tenor yield, in percentage points.

    A negative spread is an inverted curve over that segment.
    """
    return (yields[long] - yields[short]).dropna().rename(f"{long}-{short}")
