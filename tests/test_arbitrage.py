"""Unit tests for static arbitrage checks on option prices."""

import numpy as np
import pytest

from quant_finance.options.arbitrage import static_arbitrage_violations
from quant_finance.pricing.black_scholes import black_scholes_price

STRIKES = [80.0, 90.0, 100.0, 110.0, 120.0]


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("sigma", [0.05, 0.2, 0.8])
def test_black_scholes_prices_are_arbitrage_free(option_type, sigma):
    prices = black_scholes_price(
        100, np.array(STRIKES), 1, 0.05, sigma, 0.02, option_type
    )

    assert static_arbitrage_violations(STRIKES, prices, option_type) == []


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("gap", [1.0, 5.0])
@pytest.mark.parametrize("sigma", [0.05, 0.25, 1.0])
@pytest.mark.parametrize("T", [1 / 365, 60 / 365, 1.0])
def test_penny_rounded_prices_pass_with_a_rounding_tolerance(
    option_type, gap, sigma, T
):
    strikes = np.arange(80.0, 120.0 + gap, gap)
    prices = np.round(
        black_scholes_price(100, strikes, T, 0.05, sigma, 0.0, option_type), 2
    )

    assert static_arbitrage_violations(strikes, prices, option_type, tol=0.015) == []


def test_strike_order_does_not_matter():
    prices = black_scholes_price(100, np.array(STRIKES), 1, 0.05, 0.2)

    assert static_arbitrage_violations(STRIKES[::-1], prices[::-1]) == []


def test_negative_price():
    (message,) = static_arbitrage_violations([100.0], [-1.0])

    assert "negative" in message


def test_call_dearer_at_a_higher_strike():
    violations = static_arbitrage_violations([90.0, 100.0], [5.0, 6.0])

    assert any("costs more" in v for v in violations)


def test_put_dearer_at_a_lower_strike():
    violations = static_arbitrage_violations([90.0, 100.0], [6.0, 5.0], "put")

    assert any("costs more" in v for v in violations)


def test_price_gap_wider_than_strike_gap():
    violations = static_arbitrage_violations([90.0, 100.0], [25.0, 12.0])

    assert any("strike gap" in v for v in violations)


def test_butterfly_with_a_net_credit_is_not_convex():
    # The page's old butterfly inputs could give 12 - 2 * 8 + 2 < 0
    violations = static_arbitrage_violations([90.0, 100.0, 110.0], [12.0, 8.0, 2.0])

    assert any("convex" in v for v in violations)


def test_duplicate_strikes_must_have_one_price():
    violations = static_arbitrage_violations([100.0, 100.0], [5.0, 6.0])

    assert any("different prices" in v for v in violations)


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError, match="same length"):
        static_arbitrage_violations([90.0, 100.0], [5.0])


def test_unknown_option_type_raises():
    with pytest.raises(ValueError, match="option_type"):
        static_arbitrage_violations([100.0], [5.0], "straddle")
