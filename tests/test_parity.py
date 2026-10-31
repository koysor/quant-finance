"""Unit tests for put-call parity calculations."""

import numpy as np
import pytest

from quant_finance.pricing.black_scholes import black_scholes_call, black_scholes_put
from quant_finance.pricing.parity import implied_call, implied_put, parity_difference

S, K, T, R, SIGMA = 105.0, 100.0, 0.75, 0.04, 0.3
CALL = black_scholes_call(S, K, T, R, SIGMA)
PUT = black_scholes_put(S, K, T, R, SIGMA)


class TestParity:
    """Tests against Black-Scholes prices, which satisfy parity."""

    def test_implied_call_recovers_black_scholes(self):
        assert implied_call(PUT, S, K, T, R) == pytest.approx(CALL)

    def test_implied_put_recovers_black_scholes(self):
        assert implied_put(CALL, S, K, T, R) == pytest.approx(PUT)

    def test_difference_is_zero_for_consistent_prices(self):
        assert parity_difference(CALL, PUT, S, K, T, R) == pytest.approx(0.0, abs=1e-10)

    def test_difference_is_positive_when_the_call_is_overpriced(self):
        assert parity_difference(CALL + 2, PUT, S, K, T, R) == pytest.approx(2.0)

    def test_difference_is_negative_when_the_put_is_overpriced(self):
        assert parity_difference(CALL, PUT + 2, S, K, T, R) == pytest.approx(-2.0)

    def test_accepts_arrays(self):
        spots = np.array([90.0, 110.0])
        puts = black_scholes_put(spots, K, T, R, SIGMA)
        np.testing.assert_allclose(
            implied_call(puts, spots, K, T, R),
            black_scholes_call(spots, K, T, R, SIGMA),
        )


class TestDividendYield:
    """Tests for the continuous dividend yield adjustment."""

    def test_zero_yield_matches_the_no_dividend_result(self):
        assert implied_put(CALL, S, K, T, R, q=0.0) == implied_put(CALL, S, K, T, R)

    def test_known_value(self):
        adjusted = 100.0 * np.exp(-0.02)
        pv_strike = 100.0 * np.exp(-0.05)
        assert implied_put(10.0, 100.0, 100.0, 1.0, 0.05, q=0.02) == pytest.approx(
            10.0 + pv_strike - adjusted
        )

    def test_dividends_raise_the_implied_put(self):
        with_dividends = implied_put(CALL, S, K, T, R, q=0.03)
        assert with_dividends > implied_put(CALL, S, K, T, R)

    def test_dividends_lower_the_implied_call(self):
        assert implied_call(PUT, S, K, T, R, q=0.03) < implied_call(PUT, S, K, T, R)

    def test_implied_prices_are_consistent_with_each_other(self):
        call = implied_call(PUT, S, K, T, R, q=0.03)
        assert implied_put(call, S, K, T, R, q=0.03) == pytest.approx(PUT)
