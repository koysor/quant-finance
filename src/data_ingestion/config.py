"""
Configuration management for the data ingestion package.

Provides centralized configuration for caching, rate limiting,
retry behavior, and data validation.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DataIngestionConfig:
    """Configuration for data ingestion package.

    All settings can be overridden via environment variables with
    the prefix QUANT_FINANCE_.

    Attributes:
        cache_dir: Directory for cache database
        cache_db_name: DuckDB database filename
        default_ttl_seconds: Default cache TTL in seconds
        rate_limit_per_second: Maximum API requests per second
        rate_limit_burst: Maximum burst requests allowed
        max_retries: Maximum retry attempts for failed requests
        retry_base_delay: Base delay in seconds for retry backoff
        retry_max_delay: Maximum delay in seconds for retry backoff
        validate_data: Whether to validate fetched data
        allow_partial_data: Whether to allow partial/incomplete data
        auto_adjust: yfinance auto-adjust prices setting
        threads: Whether yfinance should use threads for downloads
    """

    # Cache settings
    cache_dir: str = field(
        default_factory=lambda: os.path.expanduser("~/.quant_finance")
    )
    cache_db_name: str = "cache.duckdb"
    default_ttl_seconds: int = 3600  # 1 hour

    # Rate limiting
    rate_limit_per_second: float = 2.0
    rate_limit_burst: int = 10

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    # Data validation
    validate_data: bool = True
    allow_partial_data: bool = False

    # yfinance settings
    auto_adjust: bool = True
    threads: bool = True

    @property
    def cache_db_path(self) -> str:
        """Get full path to cache database."""
        return os.path.join(self.cache_dir, self.cache_db_name)

    def ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "DataIngestionConfig":
        """Create configuration from environment variables.

        Environment variables:
            QUANT_FINANCE_CACHE_DIR: Cache directory path
            QUANT_FINANCE_CACHE_TTL: Default TTL in seconds
            QUANT_FINANCE_RATE_LIMIT: Requests per second
            QUANT_FINANCE_RATE_LIMIT_BURST: Burst capacity
            QUANT_FINANCE_MAX_RETRIES: Maximum retry attempts
            QUANT_FINANCE_VALIDATE_DATA: Enable/disable validation (true/false)

        Returns:
            DataIngestionConfig with values from environment

        Example:
            >>> os.environ['QUANT_FINANCE_CACHE_TTL'] = '7200'
            >>> config = DataIngestionConfig.from_env()
            >>> config.default_ttl_seconds
            7200
        """
        config = cls()

        # Cache settings
        if cache_dir := os.getenv("QUANT_FINANCE_CACHE_DIR"):
            config.cache_dir = os.path.expanduser(cache_dir)
        if cache_ttl := os.getenv("QUANT_FINANCE_CACHE_TTL"):
            config.default_ttl_seconds = int(cache_ttl)

        # Rate limiting
        if rate_limit := os.getenv("QUANT_FINANCE_RATE_LIMIT"):
            config.rate_limit_per_second = float(rate_limit)
        if burst := os.getenv("QUANT_FINANCE_RATE_LIMIT_BURST"):
            config.rate_limit_burst = int(burst)

        # Retry settings
        if max_retries := os.getenv("QUANT_FINANCE_MAX_RETRIES"):
            config.max_retries = int(max_retries)
        if base_delay := os.getenv("QUANT_FINANCE_RETRY_BASE_DELAY"):
            config.retry_base_delay = float(base_delay)
        if max_delay := os.getenv("QUANT_FINANCE_RETRY_MAX_DELAY"):
            config.retry_max_delay = float(max_delay)

        # Validation
        if validate := os.getenv("QUANT_FINANCE_VALIDATE_DATA"):
            config.validate_data = validate.lower() in ("true", "1", "yes")

        return config

    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"DataIngestionConfig(\n"
            f"  cache_dir={self.cache_dir}\n"
            f"  cache_db_path={self.cache_db_path}\n"
            f"  default_ttl_seconds={self.default_ttl_seconds}\n"
            f"  rate_limit_per_second={self.rate_limit_per_second}\n"
            f"  max_retries={self.max_retries}\n"
            f"  validate_data={self.validate_data}\n"
            f")"
        )


# Global default configuration instance
_default_config: Optional[DataIngestionConfig] = None


def get_default_config() -> DataIngestionConfig:
    """Get the global default configuration.

    Creates a new configuration from environment variables on first call,
    then returns the cached instance on subsequent calls.

    Returns:
        Global DataIngestionConfig instance
    """
    global _default_config
    if _default_config is None:
        _default_config = DataIngestionConfig.from_env()
    return _default_config


def set_default_config(config: DataIngestionConfig) -> None:
    """Set the global default configuration.

    Args:
        config: Configuration instance to use as default
    """
    global _default_config
    _default_config = config
