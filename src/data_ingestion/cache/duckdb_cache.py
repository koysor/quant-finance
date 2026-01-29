"""
DuckDB-based caching implementation for data ingestion.

Provides persistent local caching with automatic expiration management.
"""

import pickle
import duckdb
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import logging

from ..base.cache import BaseCache
from ..config import DataIngestionConfig, get_default_config
from ..exceptions import CacheError

logger = logging.getLogger(__name__)


class DuckDBCache(BaseCache):
    """DuckDB-based cache implementation.

    Uses DuckDB for persistent local caching of DataFrames with
    automatic expiration management.

    Attributes:
        config: Configuration instance
        db_path: Path to DuckDB database file
        con: DuckDB connection
    """

    # Cache table schemas
    _TABLE_SCHEMAS = {
        "equity_cache": """
            CREATE TABLE IF NOT EXISTS equity_cache (
                cache_key VARCHAR PRIMARY KEY,
                symbol VARCHAR,
                start_date DATE,
                end_date DATE,
                interval VARCHAR,
                data BLOB,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """,
        "options_cache": """
            CREATE TABLE IF NOT EXISTS options_cache (
                cache_key VARCHAR PRIMARY KEY,
                symbol VARCHAR,
                expiration_date DATE,
                data BLOB,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """,
        "fixed_income_cache": """
            CREATE TABLE IF NOT EXISTS fixed_income_cache (
                cache_key VARCHAR PRIMARY KEY,
                instrument VARCHAR,
                maturity VARCHAR,
                start_date DATE,
                end_date DATE,
                data BLOB,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """,
    }

    _TABLE_INDEXES = {
        "equity_cache": [
            "CREATE INDEX IF NOT EXISTS idx_equity_symbol ON equity_cache(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_equity_expires ON equity_cache(expires_at)",
        ],
        "options_cache": [
            "CREATE INDEX IF NOT EXISTS idx_options_symbol ON options_cache(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_options_expires ON options_cache(expires_at)",
        ],
        "fixed_income_cache": [
            "CREATE INDEX IF NOT EXISTS idx_fixedincome_instrument ON fixed_income_cache(instrument)",
            "CREATE INDEX IF NOT EXISTS idx_fixedincome_expires ON fixed_income_cache(expires_at)",
        ],
    }

    def __init__(
        self,
        config: Optional[DataIngestionConfig] = None,
        db_path: Optional[str] = None,
    ):
        """Initialize DuckDB cache.

        Args:
            config: Configuration instance (uses default if None)
            db_path: Path to database file (uses config.cache_db_path if None)

        Example:
            >>> cache = DuckDBCache()
            >>> # Or with custom path
            >>> cache = DuckDBCache(db_path="/custom/path/cache.duckdb")
        """
        self.config = config or get_default_config()

        # Determine database path
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = self.config.cache_db_path

        # Ensure cache directory exists
        self.config.ensure_cache_dir()

        # Initialize connection
        self.con = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database connection and create tables."""
        try:
            self.con = duckdb.connect(self.db_path)

            # Create all cache tables
            for table_name, schema in self._TABLE_SCHEMAS.items():
                self.con.execute(schema)

                # Create indexes
                for index_sql in self._TABLE_INDEXES.get(table_name, []):
                    self.con.execute(index_sql)

            logger.info(f"Initialized DuckDB cache at {self.db_path}")

        except Exception as e:
            raise CacheError(f"Failed to initialize DuckDB cache: {e}") from e

    def get(self, cache_key: str, table: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data.

        Args:
            cache_key: Unique identifier for the cached data
            table: Cache table name

        Returns:
            DataFrame if cache hit and not expired, None otherwise

        Raises:
            CacheError: If there's an error reading from cache
        """
        try:
            # Check if table exists
            if table not in self._TABLE_SCHEMAS:
                logger.warning(f"Unknown cache table: {table}")
                return None

            # Query for the cache entry
            query = f"""
                SELECT data, expires_at
                FROM {table}
                WHERE cache_key = ?
                  AND expires_at > ?
            """

            result = self.con.execute(query, [cache_key, datetime.now()]).fetchone()

            if result is None:
                logger.debug(f"Cache miss for {cache_key} in {table}")
                return None

            # Unpickle the DataFrame
            data_blob, expires_at = result
            df = pickle.loads(data_blob)

            logger.info(f"Cache hit for {cache_key} in {table} (expires: {expires_at})")
            return df

        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            raise CacheError(f"Failed to read from cache: {e}") from e

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
            **metadata: Additional metadata (symbol, dates, etc.)

        Raises:
            CacheError: If there's an error writing to cache
        """
        try:
            # Check if table exists
            if table not in self._TABLE_SCHEMAS:
                raise CacheError(f"Unknown cache table: {table}")

            # Pickle the DataFrame
            data_blob = pickle.dumps(data)

            # Calculate expiration
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl_seconds)

            # Build insert query based on table
            if table == "equity_cache":
                query = """
                    INSERT OR REPLACE INTO equity_cache
                    (cache_key, symbol, start_date, end_date, interval,
                     data, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    cache_key,
                    metadata.get("symbol"),
                    metadata.get("start_date"),
                    metadata.get("end_date"),
                    metadata.get("interval"),
                    data_blob,
                    now,
                    expires_at,
                ]

            elif table == "options_cache":
                query = """
                    INSERT OR REPLACE INTO options_cache
                    (cache_key, symbol, expiration_date,
                     data, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                params = [
                    cache_key,
                    metadata.get("symbol"),
                    metadata.get("expiration"),
                    data_blob,
                    now,
                    expires_at,
                ]

            elif table == "fixed_income_cache":
                query = """
                    INSERT OR REPLACE INTO fixed_income_cache
                    (cache_key, instrument, maturity, start_date, end_date,
                     data, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    cache_key,
                    metadata.get("instrument"),
                    metadata.get("maturity"),
                    metadata.get("start_date"),
                    metadata.get("end_date"),
                    data_blob,
                    now,
                    expires_at,
                ]

            else:
                raise CacheError(f"Unsupported table: {table}")

            # Execute insert
            self.con.execute(query, params)

            logger.info(
                f"Cached data for {cache_key} in {table} "
                f"(TTL: {ttl_seconds}s, expires: {expires_at})"
            )

        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
            raise CacheError(f"Failed to write to cache: {e}") from e

    def invalidate(
        self, cache_key: Optional[str] = None, table: Optional[str] = None
    ) -> None:
        """Invalidate (delete) cached data.

        Args:
            cache_key: Specific key to invalidate (if None, invalidate all in table)
            table: Table to invalidate (if None, invalidate all tables)

        Raises:
            CacheError: If there's an error invalidating cache
        """
        try:
            if cache_key and table:
                # Delete specific entry
                query = f"DELETE FROM {table} WHERE cache_key = ?"
                self.con.execute(query, [cache_key])
                logger.info(f"Invalidated cache key {cache_key} in {table}")

            elif table:
                # Delete all entries in table
                if table not in self._TABLE_SCHEMAS:
                    raise CacheError(f"Unknown cache table: {table}")
                query = f"DELETE FROM {table}"
                self.con.execute(query)
                logger.info(f"Invalidated all entries in {table}")

            else:
                # Delete all entries in all tables
                for table_name in self._TABLE_SCHEMAS.keys():
                    query = f"DELETE FROM {table_name}"
                    self.con.execute(query)
                logger.info("Invalidated entire cache")

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            raise CacheError(f"Failed to invalidate cache: {e}") from e

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed

        Raises:
            CacheError: If there's an error during cleanup
        """
        try:
            total_removed = 0
            now = datetime.now()

            for table_name in self._TABLE_SCHEMAS.keys():
                # Count entries to be removed
                count_query = f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    WHERE expires_at <= ?
                """
                count = self.con.execute(count_query, [now]).fetchone()[0]

                # Delete expired entries
                delete_query = f"""
                    DELETE FROM {table_name}
                    WHERE expires_at <= ?
                """
                self.con.execute(delete_query, [now])

                if count > 0:
                    logger.info(f"Removed {count} expired entries from {table_name}")
                    total_removed += count

            return total_removed

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            raise CacheError(f"Failed to cleanup cache: {e}") from e

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics

        Example:
            >>> cache = DuckDBCache()
            >>> stats = cache.get_cache_stats()
            >>> print(f"Total entries: {stats['total_entries']}")
        """
        try:
            stats = {
                "db_path": self.db_path,
                "db_size_mb": Path(self.db_path).stat().st_size / (1024 * 1024),
                "tables": {},
            }

            total_entries = 0

            for table_name in self._TABLE_SCHEMAS.keys():
                # Count total entries
                total_query = f"SELECT COUNT(*) FROM {table_name}"
                total_count = self.con.execute(total_query).fetchone()[0]

                # Count expired entries
                expired_query = f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    WHERE expires_at <= ?
                """
                expired_count = self.con.execute(
                    expired_query, [datetime.now()]
                ).fetchone()[0]

                stats["tables"][table_name] = {
                    "total_entries": total_count,
                    "active_entries": total_count - expired_count,
                    "expired_entries": expired_count,
                }

                total_entries += total_count

            stats["total_entries"] = total_entries

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e), "db_path": self.db_path}

    def close(self) -> None:
        """Close database connection.

        Example:
            >>> cache = DuckDBCache()
            >>> # ... use cache ...
            >>> cache.close()
        """
        if self.con:
            self.con.close()
            self.con = None
            logger.info("Closed DuckDB cache connection")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"DuckDBCache(db_path={self.db_path})"
