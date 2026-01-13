"""
Data validation utilities for verifying fetched data quality.
"""

from datetime import datetime
from typing import List
import pandas as pd
import logging


logger = logging.getLogger(__name__)


class DataValidator:
    """Collection of data validation methods for different data types."""

    @staticmethod
    def validate_equity_data(df: pd.DataFrame, strict: bool = True) -> bool:
        """Validate equity/index OHLCV data.

        Args:
            df: DataFrame to validate
            strict: If True, apply strict validation (no missing values allowed)

        Returns:
            True if valid, False otherwise

        Validation checks:
            - Required columns exist
            - DataFrame not empty
            - Prices are positive
            - High >= Low for each row
            - No completely null rows
        """
        required_columns = ["Open", "High", "Low", "Close", "Volume"]

        # Check required columns exist
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            logger.error(f"Missing required columns: {missing}")
            return False

        # Check for completely empty data
        if df.empty:
            logger.error("DataFrame is empty")
            return False

        # Check for reasonable price values (positive)
        price_cols = ["Open", "High", "Low", "Close"]
        if (df[price_cols] <= 0).any().any():
            logger.error("Found non-positive prices")
            if strict:
                return False
            logger.warning("Non-positive prices found but continuing (strict=False)")

        # Check High >= Low
        if (df["High"] < df["Low"]).any():
            logger.error("Found rows where High < Low")
            return False

        # Check for completely null rows
        if df[required_columns].isnull().all(axis=1).any():
            logger.error("Found completely null rows")
            return False

        # In strict mode, check for any null values
        if strict and df[required_columns].isnull().any().any():
            null_counts = df[required_columns].isnull().sum()
            logger.error(f"Found null values in strict mode: {null_counts.to_dict()}")
            return False

        logger.debug(f"Equity data validation passed (shape: {df.shape})")
        return True

    @staticmethod
    def validate_options_data(
        calls: pd.DataFrame, puts: pd.DataFrame, strict: bool = True
    ) -> bool:
        """Validate options chain data.

        Args:
            calls: DataFrame with call options
            puts: DataFrame with put options
            strict: If True, apply strict validation

        Returns:
            True if valid, False otherwise

        Validation checks:
            - Required columns exist in both DataFrames
            - Not empty
            - Strikes are positive
            - Prices are non-negative
        """
        required_columns = ["Strike", "Last", "Volume", "OpenInterest"]

        for df, name in [(calls, "calls"), (puts, "puts")]:
            # Check required columns
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                logger.error(f"Missing required columns in {name}: {missing}")
                return False

            # Check not empty
            if df.empty:
                logger.error(f"{name.capitalize()} DataFrame is empty")
                if strict:
                    return False

            # Check strikes are positive
            if not df.empty and (df["Strike"] <= 0).any():
                logger.error(f"Found non-positive strikes in {name}")
                return False

            # Check last prices are non-negative (can be 0)
            if not df.empty and "Last" in df.columns and (df["Last"] < 0).any():
                logger.error(f"Found negative prices in {name}")
                return False

        logger.debug(
            f"Options data validation passed (calls: {len(calls)}, puts: {len(puts)})"
        )
        return True

    @staticmethod
    def validate_fixed_income_data(df: pd.DataFrame, strict: bool = True) -> bool:
        """Validate fixed income/treasury yield data.

        Args:
            df: DataFrame to validate
            strict: If True, apply strict validation

        Returns:
            True if valid, False otherwise

        Validation checks:
            - DataFrame not empty
            - Yields are non-negative (can be 0)
            - Yields are reasonable (< 100%)
        """
        # Check not empty
        if df.empty:
            logger.error("DataFrame is empty")
            return False

        # Get numeric columns (yields)
        numeric_cols = df.select_dtypes(include=["number"]).columns

        if len(numeric_cols) == 0:
            logger.error("No numeric yield columns found")
            return False

        # Check yields are non-negative
        if (df[numeric_cols] < 0).any().any():
            logger.error("Found negative yields")
            return False

        # Check yields are reasonable (< 100% as decimal, or < 10000 as basis points)
        # Assume yields > 1 are in basis points, else in decimal
        max_yield = df[numeric_cols].max().max()
        if max_yield > 1:
            # Likely basis points
            if max_yield > 10000:
                logger.error(f"Found unreasonable yield: {max_yield} bps")
                if strict:
                    return False
        else:
            # Likely decimal
            if max_yield > 1.0:
                logger.error(f"Found unreasonable yield: {max_yield * 100:.1f}%")
                if strict:
                    return False

        logger.debug(f"Fixed income data validation passed (shape: {df.shape})")
        return True

    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate that date range is reasonable.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            True if valid, False otherwise

        Validation checks:
            - Both dates can be parsed
            - End date is after start date
            - Start date is not in the future
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return False

        # End must be after start
        if end <= start:
            logger.error(f"End date {end_date} must be after start date {start_date}")
            return False

        # Start cannot be in the future
        if start > datetime.now():
            logger.error(f"Start date {start_date} is in the future")
            return False

        logger.debug(f"Date range validation passed: {start_date} to {end_date}")
        return True

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate stock/option symbol format.

        Args:
            symbol: Ticker symbol

        Returns:
            True if valid, False otherwise

        Validation checks:
            - Not empty
            - Reasonable length (1-10 characters)
            - Only alphanumeric, dots, hyphens, carets (for indices)
        """
        if not symbol or not isinstance(symbol, str):
            logger.error("Symbol is empty or not a string")
            return False

        symbol = symbol.strip()

        if len(symbol) == 0:
            logger.error("Symbol is empty after stripping")
            return False

        if len(symbol) > 10:
            logger.error(f"Symbol too long: {symbol} ({len(symbol)} chars)")
            return False

        # Allow alphanumeric, dots, hyphens, and carets (for indices like ^GSPC)
        import re

        if not re.match(r"^[A-Za-z0-9.\-^]+$", symbol):
            logger.error(f"Symbol contains invalid characters: {symbol}")
            return False

        logger.debug(f"Symbol validation passed: {symbol}")
        return True

    @staticmethod
    def validate_interval(interval: str) -> bool:
        """Validate data interval format.

        Args:
            interval: Interval string (e.g., '1d', '1h', '5m')

        Returns:
            True if valid, False otherwise
        """
        valid_intervals = [
            "1m",
            "2m",
            "5m",
            "15m",
            "30m",
            "60m",
            "90m",
            "1h",
            "1d",
            "5d",
            "1wk",
            "1mo",
            "3mo",
        ]

        if interval not in valid_intervals:
            logger.error(
                f"Invalid interval: {interval}. Must be one of {valid_intervals}"
            )
            return False

        logger.debug(f"Interval validation passed: {interval}")
        return True


def validate_dataframe_not_empty(df: pd.DataFrame, name: str = "DataFrame") -> bool:
    """Quick validation that DataFrame is not empty.

    Args:
        df: DataFrame to check
        name: Name for logging

    Returns:
        True if not empty, False otherwise
    """
    if df is None:
        logger.error(f"{name} is None")
        return False

    if df.empty:
        logger.error(f"{name} is empty")
        return False

    return True


def validate_required_columns(
    df: pd.DataFrame, required_columns: List[str], name: str = "DataFrame"
) -> bool:
    """Validate that DataFrame has required columns.

    Args:
        df: DataFrame to check
        required_columns: List of required column names
        name: Name for logging

    Returns:
        True if all columns present, False otherwise
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        logger.error(f"{name} missing required columns: {missing}")
        return False

    return True
