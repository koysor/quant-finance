"""Unit tests for the DuckDB-backed data ingestion cache."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.data_ingestion.cache.duckdb_cache import DuckDBCache
from src.data_ingestion.config import DataIngestionConfig
from src.data_ingestion.exceptions import CacheError


@pytest.fixture
def config(tmp_path):
    """Configuration pointing the cache at a temporary directory."""
    return DataIngestionConfig(cache_dir=str(tmp_path))


@pytest.fixture
def cache(config):
    """Fresh cache backed by a temporary database file."""
    cache = DuckDBCache(config=config)
    yield cache
    cache.close()


@pytest.fixture
def prices():
    """Small price DataFrame with a date index."""
    return pd.DataFrame(
        {"Close": [100.0, 101.5, 99.75], "Volume": [1000, 1200, 900]},
        index=pd.date_range("2024-01-02", periods=3, freq="D", name="Date"),
    )


def equity_metadata():
    return {
        "symbol": "AAPL",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "interval": "1d",
    }


class TestInitialisation:
    """Tests for creating the cache database."""

    def test_creates_database_file(self, cache, config):
        assert cache.db_path == config.cache_db_path
        assert Path(cache.db_path).exists()

    def test_creates_all_tables(self, cache):
        tables = {row[0] for row in cache.con.execute("SHOW TABLES").fetchall()}
        assert tables == set(DuckDBCache._TABLE_SCHEMAS)

    def test_explicit_db_path_overrides_config(self, config, tmp_path):
        db_path = str(tmp_path / "custom.duckdb")
        cache = DuckDBCache(config=config, db_path=db_path)
        try:
            assert cache.db_path == db_path
        finally:
            cache.close()

    def test_invalid_path_raises_cache_error(self, config, tmp_path):
        with pytest.raises(CacheError):
            DuckDBCache(config=config, db_path=str(tmp_path / "missing" / "x.db"))


class TestGetAndSet:
    """Tests for storing and retrieving DataFrames."""

    def test_round_trip_equity(self, cache, prices):
        cache.set("AAPL_1d", prices, "equity_cache", 3600, **equity_metadata())
        pd.testing.assert_frame_equal(cache.get("AAPL_1d", "equity_cache"), prices)

    def test_round_trip_options(self, cache):
        chain = pd.DataFrame({"strike": [95.0, 100.0], "lastPrice": [6.1, 2.4]})
        cache.set(
            "AAPL_opts",
            chain,
            "options_cache",
            3600,
            symbol="AAPL",
            expiration=date(2024, 6, 21),
        )
        pd.testing.assert_frame_equal(cache.get("AAPL_opts", "options_cache"), chain)

    def test_round_trip_fixed_income(self, cache, prices):
        cache.set(
            "UST_10Y",
            prices,
            "fixed_income_cache",
            3600,
            instrument="treasury",
            maturity="10Y",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        pd.testing.assert_frame_equal(
            cache.get("UST_10Y", "fixed_income_cache"), prices
        )

    def test_metadata_is_stored(self, cache, prices):
        cache.set("AAPL_1d", prices, "equity_cache", 3600, **equity_metadata())
        row = cache.con.execute(
            "SELECT symbol, start_date, end_date, interval FROM equity_cache"
        ).fetchone()
        assert row == ("AAPL", date(2024, 1, 1), date(2024, 12, 31), "1d")

    def test_missing_key_returns_none(self, cache):
        assert cache.get("absent", "equity_cache") is None

    def test_unknown_table_on_get_returns_none(self, cache):
        assert cache.get("AAPL_1d", "no_such_table") is None

    def test_unknown_table_on_set_raises(self, cache, prices):
        with pytest.raises(CacheError):
            cache.set("AAPL_1d", prices, "no_such_table", 3600)

    def test_set_overwrites_existing_key(self, cache, prices):
        cache.set("AAPL_1d", prices, "equity_cache", 3600, **equity_metadata())
        updated = prices * 2
        cache.set("AAPL_1d", updated, "equity_cache", 3600, **equity_metadata())

        pd.testing.assert_frame_equal(cache.get("AAPL_1d", "equity_cache"), updated)
        count = cache.con.execute("SELECT COUNT(*) FROM equity_cache").fetchone()[0]
        assert count == 1

    def test_keys_are_isolated_between_tables(self, cache, prices):
        cache.set("shared", prices, "equity_cache", 3600, **equity_metadata())
        assert cache.get("shared", "options_cache") is None

    def test_corrupt_blob_raises_cache_error(self, cache, prices):
        cache.set("AAPL_1d", prices, "equity_cache", 3600, **equity_metadata())
        cache.con.execute("UPDATE equity_cache SET data = 'not a pickle'::BLOB")
        with pytest.raises(CacheError):
            cache.get("AAPL_1d", "equity_cache")


class TestExpiry:
    """Tests for TTL handling and expired-entry cleanup."""

    def test_expired_entry_is_a_miss(self, cache, prices):
        cache.set("AAPL_1d", prices, "equity_cache", -1, **equity_metadata())
        assert cache.get("AAPL_1d", "equity_cache") is None

    def test_cleanup_removes_only_expired(self, cache, prices):
        cache.set("old", prices, "equity_cache", -1, **equity_metadata())
        cache.set("new", prices, "equity_cache", 3600, **equity_metadata())
        cache.set("old_opts", prices, "options_cache", -1, symbol="AAPL")

        assert cache.cleanup_expired() == 2
        assert cache.get("new", "equity_cache") is not None
        remaining = cache.con.execute("SELECT cache_key FROM equity_cache").fetchall()
        assert remaining == [("new",)]

    def test_cleanup_with_nothing_expired(self, cache, prices):
        cache.set("new", prices, "equity_cache", 3600, **equity_metadata())
        assert cache.cleanup_expired() == 0


class TestInvalidate:
    """Tests for deleting cache entries."""

    @pytest.fixture
    def populated(self, cache, prices):
        cache.set("a", prices, "equity_cache", 3600, **equity_metadata())
        cache.set("b", prices, "equity_cache", 3600, **equity_metadata())
        cache.set("c", prices, "options_cache", 3600, symbol="AAPL")
        return cache

    def test_invalidate_single_key(self, populated):
        populated.invalidate("a", "equity_cache")
        assert populated.get("a", "equity_cache") is None
        assert populated.get("b", "equity_cache") is not None

    def test_invalidate_table(self, populated):
        populated.invalidate(table="equity_cache")
        assert populated.get("b", "equity_cache") is None
        assert populated.get("c", "options_cache") is not None

    def test_invalidate_everything(self, populated):
        populated.invalidate()
        assert populated.get_cache_stats()["total_entries"] == 0

    def test_invalidate_unknown_table_raises(self, populated):
        with pytest.raises(CacheError):
            populated.invalidate(table="no_such_table")


class TestStatsAndPersistence:
    """Tests for statistics and on-disk persistence."""

    def test_stats_count_active_and_expired(self, cache, prices):
        cache.set("old", prices, "equity_cache", -1, **equity_metadata())
        cache.set("new", prices, "equity_cache", 3600, **equity_metadata())

        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 2
        assert stats["tables"]["equity_cache"] == {
            "total_entries": 2,
            "active_entries": 1,
            "expired_entries": 1,
        }
        assert stats["tables"]["options_cache"]["total_entries"] == 0

    def test_data_survives_reopen(self, config, prices):
        first = DuckDBCache(config=config)
        first.set("AAPL_1d", prices, "equity_cache", 3600, **equity_metadata())
        first.close()

        second = DuckDBCache(config=config)
        try:
            pd.testing.assert_frame_equal(second.get("AAPL_1d", "equity_cache"), prices)
        finally:
            second.close()

    def test_close_is_idempotent(self, cache):
        cache.close()
        cache.close()
        assert cache.con is None
