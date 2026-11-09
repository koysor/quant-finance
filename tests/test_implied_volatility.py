"""Unit tests for the Black-Scholes implied volatility solver."""

import numpy as np
import pytest

from quant_finance.pricing.black_scholes import black_scholes_price, implied_volatility


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("sigma", [0.05, 0.2, 0.6, 1.5])
@pytest.mark.parametrize("S", [70.0, 100.0, 140.0])
@pytest.mark.parametrize("q", [0.0, 0.02])
def test_recovers_the_volatility_used_to_price(option_type, sigma, S, q):
    price = black_scholes_price(S, 100, 0.5, 0.04, sigma, q, option_type)
    implied = implied_volatility(price, S, 100, 0.5, 0.04, q, option_type)

    if price <= black_scholes_price(S, 100, 0.5, 0.04, 1e-6, q, option_type):
        # Deep in the money at low volatility the price equals the intrinsic
        # value in floating point, so no volatility can be recovered
        assert np.isnan(implied)
    else:
        assert implied == pytest.approx(sigma, abs=1e-6)


def test_price_indistinguishable_from_intrinsic_gives_nan():
    # Put 30 in the money at 5% vol: vega is about 1e-20
    price = black_scholes_price(70, 100, 0.5, 0.04, 0.05, option_type="put")

    assert np.isnan(implied_volatility(price, 70, 100, 0.5, 0.04, option_type="put"))


def test_solves_a_chain_at_once():
    strikes = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
    smile = np.array([0.30, 0.26, 0.22, 0.21, 0.23])
    prices = black_scholes_price(100, strikes, 1, 0.05, smile)

    np.testing.assert_allclose(
        implied_volatility(prices, 100, strikes, 1, 0.05), smile, atol=1e-6
    )


def test_scalar_inputs_return_a_scalar():
    assert np.ndim(implied_volatility(10.45, 100, 100, 1, 0.05)) == 0


@pytest.mark.parametrize(
    "price, option_type",
    [
        (5.0, "call"),  # below the intrinsic value of a call 20 in the money
        (120.0, "call"),  # at the upper bound, S
        (-1.0, "put"),
        (np.nan, "call"),
    ],
)
def test_unattainable_prices_give_nan(price, option_type):
    assert np.isnan(implied_volatility(price, 120, 100, 1, 0.0, 0.0, option_type))


def test_expired_option_gives_nan():
    assert np.isnan(implied_volatility(10.0, 110, 100, 0.0, 0.05))


def test_unknown_option_type_raises():
    with pytest.raises(ValueError, match="option_type"):
        implied_volatility(10.0, 100, 100, 1, 0.05, option_type="digital")
