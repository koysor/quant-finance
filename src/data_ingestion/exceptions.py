"""
Custom exceptions for the data ingestion package.

Provides a hierarchy of exceptions for different error scenarios
during data fetching, caching, and validation.
"""


class DataIngestionError(Exception):
    """Base exception for all data ingestion errors.

    All custom exceptions in this package inherit from this base class.
    """

    pass


class FetchError(DataIngestionError):
    """Error occurred during data fetching from external source.

    Raised when there are issues fetching data from the API,
    such as network errors, server errors, or API-specific failures.

    Example:
        >>> raise FetchError("Failed to fetch data for symbol AAPL")
    """

    pass


class CacheError(DataIngestionError):
    """Error occurred during cache operations.

    Raised when there are issues reading from or writing to the cache,
    such as database connection failures or corruption.

    Example:
        >>> raise CacheError("Failed to write to DuckDB cache")
    """

    pass


class RateLimitError(FetchError):
    """API rate limit has been exceeded.

    Raised when the external data source responds with a rate limit
    error (typically HTTP 429) or when internal rate limiting prevents
    a request.

    Example:
        >>> raise RateLimitError("Yahoo Finance rate limit exceeded")
    """

    pass


class ValidationError(DataIngestionError):
    """Data validation failed.

    Raised when fetched data doesn't meet quality requirements,
    such as missing required columns, invalid values, or failed
    integrity checks.

    Example:
        >>> raise ValidationError("Missing required column 'Close'")
    """

    pass


class SymbolNotFoundError(FetchError):
    """Symbol or ticker was not found in data source.

    Raised when attempting to fetch data for a symbol that doesn't
    exist or is not available in the data source (typically HTTP 404).

    Example:
        >>> raise SymbolNotFoundError("Symbol 'INVALID' not found")
    """

    pass


class ConfigurationError(DataIngestionError):
    """Invalid configuration or settings.

    Raised when configuration values are invalid or incompatible.

    Example:
        >>> raise ConfigurationError("rate_limit_per_second must be positive")
    """

    pass
