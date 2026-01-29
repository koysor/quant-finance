"""
Streamlit integration helpers for data ingestion.

Provides convenient wrappers and decorators for using data fetchers
in Streamlit applications with proper caching and error handling.
"""

import time
from typing import Any, Callable, Optional, Tuple
from functools import wraps
import pandas as pd
import logging

try:
    import streamlit as st

    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

    # Mock st.cache_data for type hints
    class st:
        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func

            return decorator


from .fetchers.equity import EquityFetcher
from .fetchers.options import OptionsFetcher
from .fetchers.fixed_income import FixedIncomeFetcher
from .exceptions import (
    SymbolNotFoundError,
    RateLimitError,
    DataIngestionError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def st_cache_data_ingestion(ttl: int = 3600, show_spinner: bool = True):
    """Decorator for caching data ingestion in Streamlit.

    Combines Streamlit's cache_data with our DuckDB cache for
    optimal performance.

    Args:
        ttl: Time-to-live in seconds
        show_spinner: Whether to show loading spinner

    Returns:
        Decorator function

    Example:
        >>> @st_cache_data_ingestion(ttl=3600)
        ... def load_stock_data(symbol: str, start: str, end: str):
        ...     fetcher = EquityFetcher()
        ...     return fetcher.fetch_historical(symbol, start, end)
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available, caching disabled")

        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    def decorator(func: Callable) -> Callable:
        @st.cache_data(ttl=ttl, show_spinner=show_spinner)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


@st_cache_data_ingestion(ttl=3600)
def get_stock_data(
    symbol: str, start_date: str, end_date: str, interval: str = "1d"
) -> pd.DataFrame:
    """Cached stock data fetcher for Streamlit apps.

    Args:
        symbol: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval

    Returns:
        DataFrame with OHLCV data

    Example:
        >>> import streamlit as st
        >>> df = get_stock_data("AAPL", "2023-01-01", "2023-12-31")
        >>> st.dataframe(df)
    """
    fetcher = EquityFetcher()
    return fetcher.fetch_historical(symbol, start_date, end_date, interval)


@st_cache_data_ingestion(ttl=1800)
def get_options_chain(
    symbol: str, expiration: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Cached options chain fetcher for Streamlit apps.

    Args:
        symbol: Stock ticker symbol
        expiration: Expiration date (None for nearest)

    Returns:
        Tuple of (calls DataFrame, puts DataFrame)

    Example:
        >>> import streamlit as st
        >>> calls, puts = get_options_chain("AAPL", "2024-01-19")
        >>> st.dataframe(calls)
    """
    fetcher = OptionsFetcher()
    return fetcher.fetch_option_chain(symbol, expiration)


@st_cache_data_ingestion(ttl=21600)  # 6 hours
def get_treasury_yields(
    maturities: Optional[list] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Cached treasury yields fetcher for Streamlit apps.

    Args:
        maturities: List of maturities
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame with treasury yields

    Example:
        >>> import streamlit as st
        >>> yields = get_treasury_yields(["10Y", "30Y"], "2023-01-01", "2023-12-31")
        >>> st.line_chart(yields)
    """
    fetcher = FixedIncomeFetcher()
    return fetcher.fetch_treasury_yields(maturities, start_date, end_date)


def display_fetch_status(
    fetcher_func: Callable, *args, error_prefix: str = "Error", **kwargs
) -> Any:
    """Wrapper to display fetch status in Streamlit UI.

    Automatically handles errors and displays appropriate messages
    using Streamlit's UI elements.

    Args:
        fetcher_func: Function to execute
        *args: Positional arguments for function
        error_prefix: Prefix for error messages
        **kwargs: Keyword arguments for function

    Returns:
        Result of fetcher_func or None if error

    Example:
        >>> import streamlit as st
        >>> df = display_fetch_status(
        ...     get_stock_data,
        ...     symbol="AAPL",
        ...     start_date="2023-01-01",
        ...     end_date="2023-12-31"
        ... )
        >>> if df is not None:
        ...     st.dataframe(df)
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available, executing without UI")
        try:
            return fetcher_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    with st.spinner("Fetching data..."):
        try:
            data = fetcher_func(*args, **kwargs)
            st.success("Data loaded successfully!")
            return data

        except SymbolNotFoundError as e:
            st.error(f"{error_prefix}: Symbol not found - {e}")
            logger.error(f"Symbol not found: {e}")
            return None

        except ValidationError as e:
            st.error(f"{error_prefix}: Invalid input - {e}")
            logger.error(f"Validation error: {e}")
            return None

        except RateLimitError as e:
            st.warning("Rate limit reached. Waiting and retrying...")
            logger.warning(f"Rate limit: {e}")
            time.sleep(2)
            try:
                return fetcher_func(*args, **kwargs)
            except Exception as retry_error:
                st.error(f"{error_prefix}: Failed after retry - {retry_error}")
                return None

        except DataIngestionError as e:
            st.error(f"{error_prefix}: Failed to fetch data - {e}")
            logger.error(f"Fetch error: {e}")
            return None

        except Exception as e:
            st.error(f"{error_prefix}: Unexpected error - {e}")
            logger.exception(f"Unexpected error: {e}")
            return None


def create_stock_data_widget(
    default_symbol: str = "AAPL",
    default_start: str = "2023-01-01",
    default_end: str = "2023-12-31",
    key_prefix: str = "",
) -> Optional[pd.DataFrame]:
    """Create a complete Streamlit widget for fetching stock data.

    Includes input fields and automatic fetching with error handling.

    Args:
        default_symbol: Default symbol
        default_start: Default start date
        default_end: Default end date
        key_prefix: Prefix for widget keys (for multiple instances)

    Returns:
        DataFrame with stock data or None

    Example:
        >>> import streamlit as st
        >>> df = create_stock_data_widget()
        >>> if df is not None:
        ...     st.line_chart(df['Close'])
    """
    if not STREAMLIT_AVAILABLE:
        logger.error("Streamlit not available")
        return None

    col1, col2, col3 = st.columns(3)

    with col1:
        symbol = st.text_input(
            "Stock Symbol", value=default_symbol, key=f"{key_prefix}_symbol"
        )

    with col2:
        start_date = st.date_input(
            "Start Date", value=pd.to_datetime(default_start), key=f"{key_prefix}_start"
        )

    with col3:
        end_date = st.date_input(
            "End Date", value=pd.to_datetime(default_end), key=f"{key_prefix}_end"
        )

    if st.button("Fetch Data", key=f"{key_prefix}_fetch"):
        df = display_fetch_status(
            get_stock_data,
            symbol=symbol,
            start_date=str(start_date),
            end_date=str(end_date),
        )
        return df

    return None


def create_options_widget(
    default_symbol: str = "AAPL", key_prefix: str = ""
) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Create a complete Streamlit widget for fetching options data.

    Args:
        default_symbol: Default symbol
        key_prefix: Prefix for widget keys

    Returns:
        Tuple of (calls, puts) DataFrames or None

    Example:
        >>> import streamlit as st
        >>> result = create_options_widget()
        >>> if result:
        ...     calls, puts = result
        ...     st.dataframe(calls)
    """
    if not STREAMLIT_AVAILABLE:
        logger.error("Streamlit not available")
        return None

    symbol = st.text_input(
        "Stock Symbol", value=default_symbol, key=f"{key_prefix}_symbol"
    )

    # Get available expirations
    if symbol:
        try:
            fetcher = OptionsFetcher()
            expirations = fetcher.get_available_expirations(symbol)

            if expirations:
                expiration = st.selectbox(
                    "Expiration Date",
                    options=expirations,
                    key=f"{key_prefix}_expiration",
                )

                if st.button("Fetch Options", key=f"{key_prefix}_fetch"):
                    result = display_fetch_status(
                        get_options_chain, symbol=symbol, expiration=expiration
                    )
                    return result
            else:
                st.warning(f"No options available for {symbol}")

        except Exception as e:
            st.error(f"Error getting expirations: {e}")

    return None


def format_market_data_summary(df: pd.DataFrame) -> dict:
    """Format stock data for display in Streamlit metrics.

    Args:
        df: Stock data DataFrame

    Returns:
        Dictionary with summary metrics

    Example:
        >>> import streamlit as st
        >>> df = get_stock_data("AAPL", "2023-01-01", "2023-12-31")
        >>> summary = format_market_data_summary(df)
        >>> st.metric("Latest Close", f"${summary['latest_close']:.2f}")
    """
    if df.empty:
        return {}

    latest_close = df["Close"].iloc[-1]
    previous_close = df["Close"].iloc[-2] if len(df) > 1 else latest_close
    change = latest_close - previous_close
    change_pct = (change / previous_close) * 100 if previous_close != 0 else 0

    return {
        "latest_close": latest_close,
        "previous_close": previous_close,
        "change": change,
        "change_pct": change_pct,
        "high": df["High"].max(),
        "low": df["Low"].min(),
        "avg_volume": df["Volume"].mean(),
        "period_return": ((latest_close - df["Close"].iloc[0]) / df["Close"].iloc[0])
        * 100,
    }
