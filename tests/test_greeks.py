"""Unit tests for Black-Scholes Greeks, dividends and input validation."""

import numpy as np
import pytest

from quant_finance.pricing.black_scholes import (
    black_scholes_call,
    black_scholes_delta,
    black_scholes_gamma,
    black_scholes_price,
    black_scholes_put,
    black_scholes_rho,
    black_scholes_theta,
    black_scholes_vega,
)
from quant_finance.pricing.parity import parity_difference

TYPES = ["call", "put"]

# A grid of live options, with and without dividends
GRID = [
    (S, K, T, r, sigma, q)
    for S in (80.0, 100.0, 125.0)
    for K in (90.0, 110.0)
    for T in (0.1, 1.0, 3.0)
    for r in (0.0, 0.05)
    for sigma in (0.1, 0.4)
    for q in (0.0, 0.03)
]


class TestReferenceValues:
    """Greeks of the call with S=K=100, T=1, r=5%, sigma=20% (Hull's convention)."""

    ARGS = (100, 100, 1, 0.05, 0.2)

    def test_delta(self):
        assert black_scholes_delta(*self.ARGS) == pytest.approx(0.6368, abs=1e-4)

    def test_gamma(self):
        assert black_scholes_gamma(*self.ARGS) == pytest.approx(0.01876, abs=1e-5)

    def test_vega(self):
        assert black_scholes_vega(*self.ARGS) == pytest.approx(37.524, abs=1e-3)

    def test_theta(self):
        assert black_scholes_theta(*self.ARGS) == pytest.approx(-6.414, abs=1e-3)

    def test_rho(self):
        assert black_scholes_rho(*self.ARGS) == pytest.approx(53.232, abs=1e-3)


def central_difference(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)


@pytest.mark.parametrize("option_type", TYPES)
@pytest.mark.parametrize("S, K, T, r, sigma, q", GRID)
class TestAgainstFiniteDifferences:
    """Each Greek must match a central finite difference of the price."""

    def price(self, S, K, T, r, sigma, q, option_type):
        return black_scholes_price(S, K, T, r, sigma, q, option_type)

    def test_delta(self, S, K, T, r, sigma, q, option_type):
        numeric = central_difference(
            lambda s: self.price(s, K, T, r, sigma, q, option_type), S, 1e-4
        )
        greek = black_scholes_delta(S, K, T, r, sigma, q, option_type)
        assert greek == pytest.approx(numeric, abs=1e-6)

    def test_gamma(self, S, K, T, r, sigma, q, option_type):
        numeric = central_difference(
            lambda s: black_scholes_delta(s, K, T, r, sigma, q, option_type), S, 1e-4
        )
        assert black_scholes_gamma(S, K, T, r, sigma, q) == pytest.approx(
            numeric, abs=1e-6
        )

    def test_vega(self, S, K, T, r, sigma, q, option_type):
        numeric = central_difference(
            lambda v: self.price(S, K, T, r, v, q, option_type), sigma, 1e-5
        )
        assert black_scholes_vega(S, K, T, r, sigma, q) == pytest.approx(
            numeric, abs=1e-5
        )

    def test_theta(self, S, K, T, r, sigma, q, option_type):
        # Theta is the change as time passes, so minus the change in T
        numeric = -central_difference(
            lambda t: self.price(S, K, t, r, sigma, q, option_type), T, 1e-5
        )
        greek = black_scholes_theta(S, K, T, r, sigma, q, option_type)
        assert greek == pytest.approx(numeric, abs=1e-5)

    def test_rho(self, S, K, T, r, sigma, q, option_type):
        numeric = central_difference(
            lambda rate: self.price(S, K, T, rate, sigma, q, option_type), r, 1e-6
        )
        greek = black_scholes_rho(S, K, T, r, sigma, q, option_type)
        assert greek == pytest.approx(numeric, abs=1e-5)


class TestCallPutRelations:
    S, K, T, r, sigma, q = np.meshgrid(
        [80.0, 100.0, 125.0], [90.0, 110.0], [0.1, 2.0], [0.05], [0.25], [0.0, 0.03]
    )

    def args(self):
        return self.S, self.K, self.T, self.r, self.sigma, self.q

    def test_deltas_differ_by_discounted_one(self):
        call = black_scholes_delta(*self.args(), "call")
        put = black_scholes_delta(*self.args(), "put")
        np.testing.assert_allclose(call - put, np.exp(-self.q * self.T), atol=1e-12)

    def test_parity_holds_with_dividends(self):
        call = black_scholes_call(*self.args())
        put = black_scholes_put(*self.args())
        np.testing.assert_allclose(
            parity_difference(call, put, self.S, self.K, self.T, self.r, self.q),
            0.0,
            atol=1e-10,
        )

    def test_dividends_lower_calls_and_raise_puts(self):
        S, K, T, r, sigma, _ = self.args()
        assert np.all(
            black_scholes_call(S, K, T, r, sigma, 0.03)
            < black_scholes_call(S, K, T, r, sigma)
        )
        assert np.all(
            black_scholes_put(S, K, T, r, sigma, 0.03)
            > black_scholes_put(S, K, T, r, sigma)
        )


class TestDegenerateInputs:
    """Greeks of expired or zero-volatility options are finite and correct."""

    @pytest.mark.parametrize("T, sigma", [(0.0, 0.2), (1.0, 0.0)])
    @pytest.mark.parametrize(
        "S, call_delta, put_delta", [(150.0, 1.0, 0.0), (50.0, 0.0, -1.0)]
    )
    def test_delta_is_certain(self, T, sigma, S, call_delta, put_delta):
        assert black_scholes_delta(S, 100, T, 0.05, sigma) == call_delta
        assert black_scholes_delta(S, 100, T, 0.05, sigma, option_type="put") == (
            put_delta
        )

    @pytest.mark.parametrize("greek", [black_scholes_gamma, black_scholes_vega])
    @pytest.mark.parametrize("T, sigma", [(0.0, 0.2), (1.0, 0.0)])
    def test_gamma_and_vega_are_zero(self, greek, T, sigma):
        assert greek(100, 100, T, 0.05, sigma) == 0.0

    @pytest.mark.parametrize(
        "greek", [black_scholes_delta, black_scholes_theta, black_scholes_rho]
    )
    def test_no_nans_at_the_forward_without_volatility(self, greek):
        # S = K * exp(-r * T) puts the forward exactly at the strike
        assert np.isfinite(greek(100 * np.exp(-0.05), 100, 1, 0.05, 0.0))

    def test_zero_vol_theta_is_the_carry_of_intrinsic_value(self):
        # V = S - K * exp(-r * T), so theta = -dV/dT = -r * K * exp(-r * T)
        assert black_scholes_theta(150, 100, 1, 0.05, 0.0) == pytest.approx(
            -0.05 * 100 * np.exp(-0.05)
        )


class TestValidation:
    @pytest.mark.parametrize(
        "args",
        [(100, 100, 1, 0.05, -0.2), (-1, 100, 1, 0.05, 0.2), (100, -1, 1, 0.05, 0.2)],
    )
    def test_negative_inputs_raise(self, args):
        with pytest.raises(ValueError):
            black_scholes_call(*args)

    def test_unknown_option_type_raises(self):
        with pytest.raises(ValueError, match="option_type"):
            black_scholes_delta(100, 100, 1, 0.05, 0.2, option_type="straddle")

    def test_greeks_broadcast(self):
        spots = np.array([90.0, 100.0, 110.0])
        expected = [black_scholes_gamma(s, 100, 1, 0.05, 0.2) for s in spots]
        np.testing.assert_array_equal(
            black_scholes_gamma(spots, 100, 1, 0.05, 0.2), expected
        )
