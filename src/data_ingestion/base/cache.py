"""
Abstract base cache interface for data ingestion.

Defines the contract that all cache implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class BaseCache(ABC):
    """Abstract base class for cache implementations.

    All cache implementations (DuckDB, Redis, file-based, etc.)
    must inherit from this class and implement its methods.
    """

    @abstractmethod
    def get(self, cache_key: str, table: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data.

        Args:
            cache_key: Unique identifier for the cached data
            table: Cache table name (e.g., 'equity_cache', 'options_cache')

        Returns:
            DataFrame if cache hit, None if cache miss or expired

        Raises:
            CacheError: If there's an error reading from cache

        Example:
            >>> cache = DuckDBCache()
            >>> df = cache.get("equity:AAPL:2023-01-01:2023-12-31:1d", "equity_cache")
        """
        pass

    @abstractmethod
    def set(
        self,
        cache_key: str,
        data: pd.DataFrame,
        table: str,
        ttl_seconds: int,
        **metadata,
    ) -> None:
        """Store data in cache.

        Args:
            cache_key: Unique identifier for the cached data
            data: DataFrame to cache
            table: Cache table name
            ttl_seconds: Time-to-live in seconds
            **metadata: Additional metadata to store (symbol, dates, etc.)

        Raises:
            CacheError: If there's an error writing to cache

        Example:
            >>> cache.set(
            ...     "equity:AAPL:2023-01-01:2023-12-31:1d",
            ...     df,
            ...     "equity_cache",
            ...     ttl_seconds=3600,
            ...     symbol="AAPL",
            ...     start_date="2023-01-01"
            ... )
        """
        pass

    @abstractmethod
    def invalidate(
        self, cache_key: Optional[str] = None, table: Optional[str] = None
    ) -> None:
        """Invalidate (delete) cached data.

        Args:
            cache_key: Specific key to invalidate (if None, invalidate all in table)
            table: Table to invalidate (if None, invalidate all tables)

        Raises:
            CacheError: If there's an error invalidating cache

        Example:
            >>> # Invalidate specific entry
            >>> cache.invalidate("equity:AAPL:2023-01-01:2023-12-31:1d", "equity_cache")
            >>> # Invalidate all equity cache
            >>> cache.invalidate(table="equity_cache")
            >>> # Invalidate entire cache
            >>> cache.invalidate()
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed

        Raises:
            CacheError: If there's an error during cleanup

        Example:
            >>> count = cache.cleanup_expired()
            >>> print(f"Removed {count} expired entries")
        """
        pass

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics (size, entry count, hit rate, etc.)

        Example:
            >>> stats = cache.get_cache_stats()
            >>> print(f"Total entries: {stats['total_entries']}")
            >>> print(f"Cache size: {stats['size_mb']:.2f} MB")
        """
        pass

    def __repr__(self) -> str:
        """String representation of cache."""
        return f"{self.__class__.__name__}()"
