"""
High-level cache lifecycle management utilities.

Provides convenient functions for managing cache cleanup,
monitoring, and maintenance.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..config import DataIngestionConfig, get_default_config
from .duckdb_cache import DuckDBCache


logger = logging.getLogger(__name__)


class CacheManager:
    """High-level cache management utilities.

    Provides convenient methods for cache cleanup, monitoring,
    and maintenance operations.
    """

    def __init__(
        self,
        cache: Optional[DuckDBCache] = None,
        config: Optional[DataIngestionConfig] = None,
    ):
        """Initialize cache manager.

        Args:
            cache: Cache instance (creates new if None)
            config: Configuration instance
        """
        self.config = config or get_default_config()
        self.cache = cache or DuckDBCache(config=self.config)

    def cleanup_expired_entries(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of entries removed

        Example:
            >>> manager = CacheManager()
            >>> removed = manager.cleanup_expired_entries()
            >>> print(f"Removed {removed} expired entries")
        """
        logger.info("Starting cache cleanup...")
        count = self.cache.cleanup_expired()
        logger.info(f"Cache cleanup complete. Removed {count} entries.")
        return count

    def get_summary(self) -> Dict[str, Any]:
        """Get detailed cache summary with statistics.

        Returns:
            Dictionary with cache summary information

        Example:
            >>> manager = CacheManager()
            >>> summary = manager.get_summary()
            >>> print(f"Cache size: {summary['size_mb']:.2f} MB")
            >>> print(f"Total entries: {summary['total_entries']}")
        """
        stats = self.cache.get_cache_stats()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "db_path": stats.get("db_path"),
            "size_mb": stats.get("db_size_mb", 0),
            "total_entries": stats.get("total_entries", 0),
            "tables": stats.get("tables", {}),
        }

        # Calculate totals across tables
        total_active = 0
        total_expired = 0

        for table_stats in stats.get("tables", {}).values():
            total_active += table_stats.get("active_entries", 0)
            total_expired += table_stats.get("expired_entries", 0)

        summary["active_entries"] = total_active
        summary["expired_entries"] = total_expired

        return summary

    def print_summary(self) -> None:
        """Print formatted cache summary to console.

        Example:
            >>> manager = CacheManager()
            >>> manager.print_summary()
            Cache Summary
            =============
            Location: /home/user/.quant_finance/cache.duckdb
            Size: 2.45 MB
            Total Entries: 150
            Active: 142
            Expired: 8
            ...
        """
        summary = self.get_summary()

        print("\nCache Summary")
        print("=" * 50)
        print(f"Location: {summary['db_path']}")
        print(f"Size: {summary['size_mb']:.2f} MB")
        print(f"Total Entries: {summary['total_entries']}")
        print(f"Active: {summary['active_entries']}")
        print(f"Expired: {summary['expired_entries']}")
        print()

        print("By Table:")
        print("-" * 50)
        for table_name, table_stats in summary["tables"].items():
            print(f"  {table_name}:")
            print(f"    Total: {table_stats['total_entries']}")
            print(f"    Active: {table_stats['active_entries']}")
            print(f"    Expired: {table_stats['expired_entries']}")
        print()

    def invalidate_all(self, confirm: bool = False) -> None:
        """Invalidate entire cache (clear all tables).

        Args:
            confirm: Must be True to actually clear cache (safety check)

        Example:
            >>> manager = CacheManager()
            >>> manager.invalidate_all(confirm=True)
        """
        if not confirm:
            logger.warning(
                "Cache invalidation requires confirm=True. Nothing was deleted."
            )
            return

        logger.warning("Invalidating entire cache...")
        self.cache.invalidate()
        logger.info("Cache invalidated successfully")

    def invalidate_table(self, table: str, confirm: bool = False) -> None:
        """Invalidate specific cache table.

        Args:
            table: Table name to invalidate
            confirm: Must be True to actually clear (safety check)

        Example:
            >>> manager = CacheManager()
            >>> manager.invalidate_table("equity_cache", confirm=True)
        """
        if not confirm:
            logger.warning(
                f"Table invalidation requires confirm=True. {table} was not cleared."
            )
            return

        logger.warning(f"Invalidating table {table}...")
        self.cache.invalidate(table=table)
        logger.info(f"Table {table} invalidated successfully")

    def auto_cleanup_if_needed(
        self, max_expired_ratio: float = 0.2, min_expired_count: int = 10
    ) -> bool:
        """Automatically cleanup if expired entries exceed threshold.

        Args:
            max_expired_ratio: Trigger cleanup if expired > this ratio of total
            min_expired_count: Only cleanup if at least this many expired

        Returns:
            True if cleanup was performed, False otherwise

        Example:
            >>> manager = CacheManager()
            >>> # Cleanup if > 20% of entries are expired
            >>> if manager.auto_cleanup_if_needed(max_expired_ratio=0.2):
            ...     print("Auto-cleanup performed")
        """
        summary = self.get_summary()

        total = summary["total_entries"]
        expired = summary["expired_entries"]

        if total == 0:
            return False

        expired_ratio = expired / total

        if expired >= min_expired_count and expired_ratio >= max_expired_ratio:
            logger.info(
                f"Auto-cleanup triggered: {expired}/{total} "
                f"({expired_ratio:.1%}) entries expired"
            )
            self.cleanup_expired_entries()
            return True

        return False


def create_cache_manager(config: Optional[DataIngestionConfig] = None) -> CacheManager:
    """Create a cache manager instance.

    Convenience function for creating cache managers.

    Args:
        config: Configuration instance

    Returns:
        CacheManager instance

    Example:
        >>> manager = create_cache_manager()
        >>> manager.print_summary()
    """
    return CacheManager(config=config)
