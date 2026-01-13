"""
Data ingestion package for quantitative finance applications.

This package provides production-ready data fetchers for financial market data
with built-in caching, rate limiting, and error handling.

Main Components:
    - EquityFetcher: Fetch stock and index data from Yahoo Finance
    - OptionsFetcher: Fetch options chains and Greeks
    - FixedIncomeFetcher: Fetch treasury yields and bond data
    - DuckDBCache: Persistent local caching with DuckDB
    - CacheManager: High-level cache management utilities

Quick Start:
    >>> from src.data_ingestion import EquityFetcher
    >>>
    >>> # Fetch stock data with automatic caching
    >>> fetcher = EquityFetcher()
    >>> df = fetcher.fetch_historical("AAPL", "2023-01-01", "2023-12-31")
    >>> print(df.head())

Features:
    - Automatic caching with DuckDB (reduces API calls)
    - Rate limiting (respects API limits)
    - Exponential backoff retry logic
    - Data validation
    - Streamlit integration helpers
    - Comprehensive error handling

Example with Options:
    >>> from src.data_ingestion import OptionsFetcher
    >>>
    >>> fetcher = OptionsFetcher()
    >>> calls, puts = fetcher.fetch_option_chain("AAPL", "2024-01-19")
    >>> print(f"Found {len(calls)} call options")

Example with Treasury Yields:
    >>> from src.data_ingestion import FixedIncomeFetcher
    >>>
    >>> fetcher = FixedIncomeFetcher()
    >>> yields = fetcher.fetch_treasury_yields(
    ...     maturities=["10Y", "30Y"],
    ...     start_date="2023-01-01",
    ...     end_date="2023-12-31"
    ... )
    >>> print(yields.head())

Streamlit Integration:
    >>> import streamlit as st
    >>> from src.data_ingestion.streamlit_helpers import get_stock_data
    >>>
    >>> # Automatically cached for Streamlit
    >>> df = get_stock_data("AAPL", "2023-01-01", "2023-12-31")
    >>> st.dataframe(df)
"""

import logging

# Version
__version__ = "0.1.0"

# Configuration
from .config import DataIngestionConfig, get_default_config, set_default_config

# Fetchers
from .fetchers.equity import EquityFetcher
from .fetchers.options import OptionsFetcher
from .fetchers.fixed_income import FixedIncomeFetcher

# Cache
from .cache.duckdb_cache import DuckDBCache
from .cache.cache_manager import CacheManager, create_cache_manager

# Exceptions
from .exceptions import (
    DataIngestionError,
    FetchError,
    CacheError,
    RateLimitError,
    ValidationError,
    SymbolNotFoundError,
    ConfigurationError,
)

# Utilities
from .utils.validators import DataValidator
from .utils.rate_limiter import TokenBucketLimiter
from .utils.retry import ExponentialBackoffRetry, retry_on_exception


__all__ = [
    # Version
    "__version__",
    # Configuration
    "DataIngestionConfig",
    "get_default_config",
    "set_default_config",
    # Fetchers
    "EquityFetcher",
    "OptionsFetcher",
    "FixedIncomeFetcher",
    # Cache
    "DuckDBCache",
    "CacheManager",
    "create_cache_manager",
    # Exceptions
    "DataIngestionError",
    "FetchError",
    "CacheError",
    "RateLimitError",
    "ValidationError",
    "SymbolNotFoundError",
    "ConfigurationError",
    # Utilities
    "DataValidator",
    "TokenBucketLimiter",
    "ExponentialBackoffRetry",
    "retry_on_exception",
]


# Configure logging
def _configure_logging(level: int = logging.INFO):
    """Configure package logging.

    Args:
        level: Logging level (default: INFO)
    """
    logger = logging.getLogger(__name__)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False


# Initialize default logging
_configure_logging()


# Package metadata
__author__ = "Quantitative Finance Project"
__description__ = (
    "Data ingestion package for financial market data with caching and rate limiting"
)
__license__ = "MIT"
