"""Unit tests for fetcher error handling, retries, rate limiting and cache keys.

yfinance is replaced with fakes, so these tests need no network.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from quant_finance.data_ingestion.base import fetcher as base_fetcher
from quant_finance.data_ingestion.config import DataIngestionConfig
from quant_finance.data_ingestion.exceptions import (
    FetchError,
    NoDataError,
    SymbolNotFoundError,
    ValidationError,
)
from quant_finance.data_ingestion.fetchers import equity, fixed_income, options
from quant_finance.data_ingestion.fetchers.equity import EquityFetcher
from quant_finance.data_ingestion.fetchers.fixed_income import FixedIncomeFetcher
from quant_finance.data_ingestion.fetchers.options import OptionsFetcher
from quant_finance.data_ingestion.utils import retry
from quant_finance.data_ingestion.utils.retry import retry_on_exception
from quant_finance.data_ingestion.utils.validators import DataValidator

START, END = "2024-01-01", "2024-02-01"


@pytest.fixture(autouse=True)
def no_sleep_and_fresh_limiters(monkeypatch):
    """Skip retry back-off sleeps and give each test its own rate limiters."""
    monkeypatch.setattr(retry.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(base_fetcher, "_shared_limiters", {})


@pytest.fixture
def config(tmp_path):
    """Configuration with a temporary cache and a generous rate limit."""
    return DataIngestionConfig(
        cache_dir=str(tmp_path), rate_limit_per_second=1000.0, max_retries=3
    )


def ohlcv(close=100.0):
    """Small valid OHLCV frame."""
    return pd.DataFrame(
        {
            "Open": [close] * 3,
            "High": [close + 1] * 3,
            "Low": [close - 1] * 3,
            "Close": [close] * 3,
            "Volume": [1000] * 3,
        },
        index=pd.date_range("2024-01-02", periods=3, name="Date"),
    )


class FakeDownload:
    """Stand-in for yf.download that plays back a list of results.

    Each item is either returned or, if it is an exception, raised.
    """

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, symbol, **kwargs):
        self.calls.append(symbol)
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result


def patch_download(monkeypatch, module, *results):
    fake = FakeDownload(*results)
    monkeypatch.setattr(module.yf, "download", fake)
    return fake


class TestEquityCacheKey:
    def test_adjusted_and_raw_prices_use_different_keys(self, tmp_path):
        adjusted = EquityFetcher(DataIngestionConfig(cache_dir=str(tmp_path)))
        raw = EquityFetcher(
            DataIngestionConfig(cache_dir=str(tmp_path), auto_adjust=False)
        )
        args = dict(symbol="AAPL", start_date=START, end_date=END, interval="1d")

        assert adjusted._build_cache_key(**args) != raw._build_cache_key(**args)

    def test_key_is_versioned(self, config):
        key = EquityFetcher(config)._build_cache_key(
            symbol="AAPL", start_date=START, end_date=END
        )

        assert (
            key == f"equity:{base_fetcher.CACHE_KEY_VERSION}:AAPL:{START}:{END}:1d:adj"
        )


class TestEquityErrorHandling:
    def test_empty_response_raises_no_data_without_retrying(self, monkeypatch, config):
        fake = patch_download(monkeypatch, equity, pd.DataFrame())

        with pytest.raises(NoDataError):
            EquityFetcher(config).fetch_historical(
                "ZZZZZZ", START, END, use_cache=False
            )
        assert len(fake.calls) == 1

    def test_not_found_error_is_classified_and_not_retried(self, monkeypatch, config):
        fake = patch_download(monkeypatch, equity, RuntimeError("HTTP 404 Not Found"))

        with pytest.raises(SymbolNotFoundError):
            EquityFetcher(config).fetch_historical(
                "ZZZZZZ", START, END, use_cache=False
            )
        assert len(fake.calls) == 1

    def test_transient_errors_are_retried_until_success(self, monkeypatch, config):
        fake = patch_download(
            monkeypatch,
            equity,
            ConnectionError("connection reset"),
            RuntimeError("503 Service Unavailable"),
            ohlcv(),
        )

        df = EquityFetcher(config).fetch_historical("AAPL", START, END, use_cache=False)

        assert len(fake.calls) == 3
        pd.testing.assert_frame_equal(df, ohlcv())

    def test_gives_up_after_max_retries(self, monkeypatch, config):
        fake = patch_download(monkeypatch, equity, RuntimeError("502 Bad Gateway"))

        with pytest.raises(FetchError, match="Server error"):
            EquityFetcher(config).fetch_historical("AAPL", START, END, use_cache=False)
        assert len(fake.calls) == config.max_retries + 1


class TestRateLimiting:
    def test_each_attempt_takes_a_token(self, monkeypatch, config):
        patch_download(
            monkeypatch,
            equity,
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            ohlcv(),
        )
        fetcher = EquityFetcher(config)
        acquired = []
        original = fetcher.rate_limiter.acquire
        monkeypatch.setattr(
            fetcher.rate_limiter,
            "acquire",
            lambda *args, **kwargs: acquired.append(1) or original(*args, **kwargs),
        )

        fetcher.fetch_historical("AAPL", START, END, use_cache=False)

        assert len(acquired) == 3

    def test_fetchers_with_the_same_settings_share_a_limiter(self, config):
        assert (
            EquityFetcher(config).rate_limiter
            is FixedIncomeFetcher(config).rate_limiter
        )

    def test_different_settings_get_different_limiters(self, tmp_path):
        slow = DataIngestionConfig(cache_dir=str(tmp_path), rate_limit_per_second=1.0)
        fast = DataIngestionConfig(cache_dir=str(tmp_path), rate_limit_per_second=5.0)

        assert EquityFetcher(slow).rate_limiter is not EquityFetcher(fast).rate_limiter


class TestTreasuryTenors:
    def test_every_tenor_has_its_own_series(self):
        symbols = list(FixedIncomeFetcher.TREASURY_SYMBOLS.values())

        assert len(symbols) == len(set(symbols))

    @pytest.mark.parametrize("maturity", ["6M", "1Y", "2Y"])
    def test_tenors_without_a_series_are_rejected_before_fetching(
        self, monkeypatch, config, maturity
    ):
        fake = patch_download(monkeypatch, fixed_income, ohlcv())

        with pytest.raises(ValidationError, match=maturity):
            FixedIncomeFetcher(config).fetch_treasury_yields(
                [maturity, "10Y"], START, END, use_cache=False
            )
        assert fake.calls == []

    def test_yield_curve_labels_match_the_series_fetched(self, monkeypatch, config):
        # Give each Yahoo symbol a distinct yield so a mislabelled tenor shows up
        yields = {"^IRX": 5.2, "^FVX": 4.1, "^TNX": 4.3, "^TYX": 4.5}
        downloaded = []

        def fake_download(symbol, **kwargs):
            downloaded.append(symbol)
            return ohlcv(close=yields[symbol])

        monkeypatch.setattr(fixed_income.yf, "download", fake_download)

        curve = FixedIncomeFetcher(config).fetch_yield_curve(
            "2024-01-04", use_cache=False
        )

        assert sorted(downloaded) == sorted(yields)
        expected = {
            maturity: yields[symbol]
            for maturity, symbol in FixedIncomeFetcher.TREASURY_SYMBOLS.items()
        }
        assert dict(zip(curve["Maturity"], curve["Yield"])) == expected


class TestRetryOnException:
    def test_retries_listed_exceptions(self):
        calls = []

        @retry_on_exception(max_retries=2, base_delay=0.01, exceptions=(ValueError,))
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("try again")
            return "ok"

        assert flaky() == "ok"
        assert len(calls) == 3

    def test_does_not_retry_other_exceptions(self):
        calls = []

        @retry_on_exception(max_retries=2, base_delay=0.01, exceptions=(ValueError,))
        def broken():
            calls.append(1)
            raise KeyError("not retryable")

        with pytest.raises(KeyError):
            broken()
        assert len(calls) == 1


class TestCacheLifetimes:
    TODAY = datetime.now(UTC).date()

    def days_ago(self, days):
        return (self.TODAY - timedelta(days=days)).isoformat()

    @pytest.mark.parametrize(
        "end_date, closed",
        [(None, False), ("not a date", False), (0, False), (1, False), (3, True)],
    )
    def test_window_is_closed(self, end_date, closed):
        if isinstance(end_date, int):
            end_date = self.days_ago(end_date)
        assert base_fetcher.window_is_closed(end_date) is closed

    def test_recent_equity_data_uses_the_default_lifetime(self, config):
        ttl = EquityFetcher(config)._ttl_seconds(end_date=self.days_ago(0))
        assert ttl == config.default_ttl_seconds

    def test_closed_adjusted_prices_are_kept_for_a_day(self, config):
        ttl = EquityFetcher(config)._ttl_seconds(end_date=self.days_ago(30))
        assert ttl == config.adjusted_closed_window_ttl_seconds

    def test_closed_raw_prices_are_kept_for_longer(self, tmp_path):
        config = DataIngestionConfig(cache_dir=str(tmp_path), auto_adjust=False)
        ttl = EquityFetcher(config)._ttl_seconds(end_date=self.days_ago(30))
        assert ttl == config.closed_window_ttl_seconds

    def test_closed_yields_are_kept_for_longer(self, config):
        fetcher = FixedIncomeFetcher(config)
        assert fetcher._ttl_seconds(end_date=self.days_ago(30)) == (
            config.closed_window_ttl_seconds
        )
        assert fetcher._ttl_seconds(end_date=None) == config.default_ttl_seconds

    def test_fetch_caches_with_the_chosen_lifetime(self, monkeypatch, config):
        patch_download(monkeypatch, equity, ohlcv())
        fetcher = EquityFetcher(config)
        fetcher.fetch_historical("AAPL", START, END)

        created, expires = fetcher.cache.con.execute(
            "SELECT created_at, expires_at FROM equity_cache"
        ).fetchone()
        lifetime = (expires - created).total_seconds()
        assert lifetime == config.adjusted_closed_window_ttl_seconds


def chain_side(strikes, last):
    """Option chain side shaped like yfinance's, with mixed column types."""
    return pd.DataFrame(
        {
            "contractSymbol": [f"AAPL{k:08.0f}" for k in strikes],
            "lastTradeDate": pd.to_datetime(
                ["2024-01-02 15:30"] * len(strikes), utc=True
            ),
            "strike": strikes,
            "lastPrice": last,
            "bid": last,
            "ask": last,
            "volume": [10.0] * len(strikes),
            "openInterest": [100] * len(strikes),
            "impliedVolatility": [0.25] * len(strikes),
            "inTheMoney": [True] * len(strikes),
        }
    )


class FakeTicker:
    """Stand-in for yf.Ticker serving one options chain."""

    calls_made = 0

    def __init__(self, symbol):
        self.options = ("2024-06-21", "2024-07-19")

    def option_chain(self, expiration):
        FakeTicker.calls_made += 1
        return SimpleNamespace(
            calls=chain_side([95.0, 100.0], [7.0, 4.0]),
            puts=chain_side([95.0, 100.0, 105.0], [2.0, 3.5, 6.5]),
        )


class TestOptionsFetcher:
    @pytest.fixture
    def fake_ticker(self, monkeypatch):
        FakeTicker.calls_made = 0
        monkeypatch.setattr(options.yf, "Ticker", FakeTicker)

    def test_returns_calls_and_puts_with_the_expiry_fetched(self, fake_ticker, config):
        calls, puts = OptionsFetcher(config).fetch_option_chain("AAPL", use_cache=False)

        assert list(calls["Strike"]) == [95.0, 100.0]
        assert list(puts["Strike"]) == [95.0, 100.0, 105.0]
        assert set(calls["Expiration"]) == {"2024-06-21"}
        assert "OptionType" not in calls.columns

    def test_chain_round_trips_through_the_cache(self, fake_ticker, config):
        fetcher = OptionsFetcher(config)
        first = fetcher.fetch_option_chain("AAPL", "2024-06-21")
        second = fetcher.fetch_option_chain("AAPL", "2024-06-21")

        assert FakeTicker.calls_made == 1
        for fetched, cached in zip(first, second):
            pd.testing.assert_frame_equal(fetched, cached)

    def test_uses_the_configured_lifetime(self, fake_ticker, config):
        fetcher = OptionsFetcher(config)
        fetcher.fetch_option_chain("AAPL", "2024-06-21")

        created, expires = fetcher.cache.con.execute(
            "SELECT created_at, expires_at FROM options_cache"
        ).fetchone()
        assert (expires - created).total_seconds() == config.options_ttl_seconds

    def test_fetch_greeks_is_deprecated(self, fake_ticker, config):
        with pytest.warns(DeprecationWarning, match="no Greeks"):
            puts = OptionsFetcher(config).fetch_greeks("AAPL", "2024-06-21", "put")

        assert len(puts) == 3


class TestUncachedCalls:
    def test_get_info_is_retried(self, monkeypatch, config):
        attempts = []

        class FlakyTicker:
            def __init__(self, symbol):
                attempts.append(symbol)
                if len(attempts) < 2:
                    raise ConnectionError("connection reset")
                self.info = {"longName": "Apple Inc.", "currentPrice": 190.0}

        monkeypatch.setattr(equity.yf, "Ticker", FlakyTicker)

        quote = EquityFetcher(config).fetch_realtime_quote("AAPL")

        assert quote["price"] == 190.0
        assert len(attempts) == 2


class TestValidators:
    @pytest.mark.parametrize("symbol", ["AAPL", "^GSPC", "BRK-B", "GBPUSD=X", "ES=F"])
    def test_valid_symbols(self, symbol):
        assert DataValidator.validate_symbol(symbol)

    @pytest.mark.parametrize("symbol", ["", "AAPL;DROP", "A" * 11])
    def test_invalid_symbols(self, symbol):
        assert not DataValidator.validate_symbol(symbol)

    @pytest.mark.parametrize(
        "yields, valid",
        [
            ([4.2, 4.5], True),
            ([-0.5, 0.1], True),
            ([4.0, 60.0], False),
            ([-8.0, 1.0], False),
        ],
    )
    def test_yield_range_in_percent(self, yields, valid):
        df = pd.DataFrame({"10Y": yields})
        assert DataValidator.validate_fixed_income_data(df) is valid
