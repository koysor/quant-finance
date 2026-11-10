"""Tests for Treasury par yields from FRED and the yield curve helpers.

The download is replaced with a fake, so these tests need no network.
"""

import io
import urllib.parse

import numpy as np
import pandas as pd
import pytest

from quant_finance.rates import treasury

# FRED's CSV layout: a holiday row with every value missing, and a tenor
# missing on one date
SAMPLE_CSV = """observation_date,DGS2,DGS10
2025-12-23,3.48,4.18
2025-12-24,3.47,4.15
2025-12-25,,
2025-12-26,3.46,
"""


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_urlopen(monkeypatch):
    """Serve SAMPLE_CSV for any request and record the URLs requested."""
    urls = []

    def urlopen(request, timeout):
        urls.append(request.full_url)
        return FakeResponse(SAMPLE_CSV.encode())

    monkeypatch.setattr(treasury.urllib.request, "urlopen", urlopen)
    return urls


class TestSeries:
    def test_tenors_and_years_match(self):
        assert list(treasury.TREASURY_SERIES) == list(treasury.TENOR_YEARS)

    def test_tenors_are_shortest_first(self):
        years = list(treasury.TENOR_YEARS.values())
        assert years == sorted(years)

    def test_every_tenor_has_its_own_series(self):
        series = list(treasury.TREASURY_SERIES.values())
        assert len(series) == len(set(series))

    def test_unknown_tenor_is_rejected(self):
        with pytest.raises(ValueError, match="4Y"):
            treasury.check_maturities(["2Y", "4Y"])


class TestUrl:
    def test_date_range_is_repeated_for_each_series(self):
        # FRED applies each date only to the series in the same position
        url = treasury.fred_csv_url(["DGS2", "DGS10"], "2024-01-01", "2024-06-30")
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

        assert query["id"] == ["DGS2,DGS10"]
        assert query["cosd"] == ["2024-01-01,2024-01-01"]
        assert query["coed"] == ["2024-06-30,2024-06-30"]

    def test_needs_a_series(self):
        with pytest.raises(ValueError):
            treasury.fred_csv_url([], "2024-01-01", "2024-06-30")


class TestParse:
    def test_holidays_are_dropped_and_gaps_kept(self):
        frame = treasury.parse_fred_csv(SAMPLE_CSV)

        assert list(frame.index.strftime("%Y-%m-%d")) == [
            "2025-12-23",
            "2025-12-24",
            "2025-12-26",
        ]
        assert frame.index.name == "Date"
        assert np.isnan(frame.loc["2025-12-26", "DGS10"])
        assert frame.loc["2025-12-23", "DGS10"] == 4.18

    def test_dots_are_missing_values(self):
        frame = treasury.parse_fred_csv("DATE,DGS10\n2020-01-01,.\n2020-01-02,1.88\n")

        assert len(frame) == 1
        assert frame["DGS10"].dtype == float


class TestFetch:
    def test_columns_are_tenors_shortest_first(self, fake_urlopen):
        yields = treasury.fetch_treasury_par_yields(
            ["10Y", "2Y"], "2025-12-23", "2025-12-26"
        )

        assert list(yields.columns) == ["2Y", "10Y"]
        assert yields.loc["2025-12-24", "2Y"] == 3.47
        assert "id=DGS2,DGS10" in fake_urlopen[0]

    def test_default_range_is_the_year_to_today(self, fake_urlopen):
        treasury.fetch_treasury_par_yields(["2Y", "10Y"])

        query = urllib.parse.parse_qs(urllib.parse.urlparse(fake_urlopen[0]).query)
        start, end = (
            pd.Timestamp(d.split(",")[0]) for d in (query["cosd"][0], query["coed"][0])
        )
        assert end == pd.Timestamp.today().normalize()
        assert start == end - pd.DateOffset(years=1)

    def test_unknown_tenor_is_rejected_before_downloading(self, fake_urlopen):
        with pytest.raises(ValueError):
            treasury.fetch_treasury_par_yields(["2Y", "4Y"])
        assert fake_urlopen == []


class TestCurve:
    @pytest.fixture
    def yields(self):
        return treasury.parse_fred_csv(SAMPLE_CSV).rename(
            columns={"DGS2": "2Y", "DGS10": "10Y"}
        )

    def test_curve_on_a_business_day(self, yields):
        curve = treasury.curve_on(yields, "2025-12-24")

        assert curve.to_dict() == {"2Y": 3.47, "10Y": 4.15}
        assert curve.name == pd.Timestamp("2025-12-24")

    def test_holiday_uses_the_previous_business_day(self, yields):
        curve = treasury.curve_on(yields, "2025-12-25")
        assert curve.name == pd.Timestamp("2025-12-24")

    def test_missing_tenor_is_left_out(self, yields):
        curve = treasury.curve_on(yields, "2025-12-26")
        assert curve.to_dict() == {"2Y": 3.46}

    def test_no_data_before_the_date(self, yields):
        with pytest.raises(ValueError, match="No yields"):
            treasury.curve_on(yields, "2025-01-01")

    def test_spread_in_percentage_points(self, yields):
        spread = treasury.yield_spread(yields, long="10Y", short="2Y")

        assert spread.name == "10Y-2Y"
        assert spread.round(2).tolist() == [0.70, 0.68]
