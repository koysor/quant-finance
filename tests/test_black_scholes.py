"""Unit tests for Black-Scholes pricing."""

import numpy as np
import pytest

from quant_finance.pricing.black_scholes import black_scholes_call, black_scholes_put


class TestReferenceValues:
    """Prices checked against published values for S=K=100, T=1, r=5%, sigma=20%."""

    def test_call(self):
        assert black_scholes_call(100, 100, 1, 0.05, 0.2) == pytest.approx(
            10.4506, abs=1e-4
        )

    def test_put(self):
        assert black_scholes_put(100, 100, 1, 0.05, 0.2) == pytest.approx(
            5.5735, abs=1e-4
        )


class TestPutCallParity:
    """C - P must equal S - K * exp(-r * T) for all inputs."""

    def test_holds_across_parameter_grid(self):
        S, K, T, r, sigma = np.meshgrid(
            [50.0, 100.0, 150.0],
            [80.0, 100.0, 120.0],
            [0.01, 0.5, 2.0],
            [0.0, 0.05, 0.1],
            [0.05, 0.2, 0.8],
        )
        call = black_scholes_call(S, K, T, r, sigma)
        put = black_scholes_put(S, K, T, r, sigma)
        np.testing.assert_allclose(call - put, S - K * np.exp(-r * T), atol=1e-10)


class TestLimits:
    """Degenerate inputs must give the known price, not NaN."""

    @pytest.mark.parametrize("T", [0.0, -1.0])
    @pytest.mark.parametrize(
        "S, expected_call, expected_put",
        [(110.0, 10.0, 0.0), (100.0, 0.0, 0.0), (90.0, 0.0, 10.0)],
    )
    def test_at_expiry_price_is_the_payoff(self, T, S, expected_call, expected_put):
        assert black_scholes_call(S, 100, T, 0.05, 0.2) == expected_call
        assert black_scholes_put(S, 100, T, 0.05, 0.2) == expected_put

    @pytest.mark.parametrize("sigma", [0.0, 1e-8])
    @pytest.mark.parametrize("S", [90.0, 100.0, 110.0])
    def test_without_volatility_price_is_discounted_intrinsic(self, S, sigma):
        discounted_strike = 100 * np.exp(-0.05)
        assert black_scholes_call(S, 100, 1, 0.05, sigma) == pytest.approx(
            max(S - discounted_strike, 0.0)
        )
        assert black_scholes_put(S, 100, 1, 0.05, sigma) == pytest.approx(
            max(discounted_strike - S, 0.0), abs=1e-9
        )

    def test_deep_in_the_money_call_approaches_forward_value(self):
        assert black_scholes_call(1e6, 100, 1, 0.05, 0.2) == pytest.approx(
            1e6 - 100 * np.exp(-0.05)
        )

    def test_call_price_is_zero_for_worthless_stock(self):
        assert black_scholes_call(0.0, 100, 1, 0.05, 0.2) == 0.0


class TestVectorisation:
    """Array inputs must match the equivalent scalar calculations."""

    @pytest.mark.parametrize("price", [black_scholes_call, black_scholes_put])
    def test_array_matches_scalars(self, price):
        spots = np.array([80.0, 100.0, 120.0])
        expected = [price(spot, 100, 1, 0.05, 0.2) for spot in spots]
        np.testing.assert_array_equal(price(spots, 100, 1, 0.05, 0.2), expected)

    @pytest.mark.parametrize("price", [black_scholes_call, black_scholes_put])
    def test_mixed_expired_and_live_inputs(self, price):
        times = np.array([0.0, 1.0])
        expected = [price(110, 100, time, 0.05, 0.2) for time in times]
        np.testing.assert_array_equal(price(110, 100, times, 0.05, 0.2), expected)

    def test_scalar_inputs_return_a_scalar(self):
        assert np.ndim(black_scholes_call(100, 100, 1, 0.05, 0.2)) == 0
