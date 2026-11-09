"""Unit tests for the Cox-Ross-Rubinstein binomial pricer."""

import pytest

from quant_finance.pricing.binomial import binomial_price, crr_parameters
from quant_finance.pricing.black_scholes import black_scholes_price


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("S", [90.0, 100.0, 110.0])
@pytest.mark.parametrize("q", [0.0, 0.03])
def test_european_price_converges_to_black_scholes(option_type, S, q):
    tree = binomial_price(S, 100, 1, 0.05, 0.25, 2000, option_type, q=q)

    assert tree == pytest.approx(
        black_scholes_price(S, 100, 1, 0.05, 0.25, q, option_type), abs=0.01
    )


def test_hull_american_put_example():
    # Hull, Options, Futures, and Other Derivatives (9th ed.), Example 21.1:
    # S=50, K=50, r=10%, sigma=40%, T=5 months, 5 steps gives 4.49
    price = binomial_price(50, 50, 5 / 12, 0.1, 0.4, 5, "put", american=True)

    assert price == pytest.approx(4.49, abs=0.005)


def test_early_exercise_adds_value_to_an_in_the_money_put():
    european = binomial_price(80, 100, 1, 0.05, 0.2, 500, "put")
    american = binomial_price(80, 100, 1, 0.05, 0.2, 500, "put", american=True)

    assert american > european
    assert american >= 100 - 80


def test_american_call_without_dividends_is_never_exercised_early():
    european = binomial_price(110, 100, 1, 0.05, 0.2, 500, "call")
    american = binomial_price(110, 100, 1, 0.05, 0.2, 500, "call", american=True)

    assert american == pytest.approx(european, abs=1e-12)


def test_american_call_with_dividends_can_be_worth_more():
    european = binomial_price(150, 100, 1, 0.01, 0.2, 500, "call", q=0.08)
    american = binomial_price(
        150, 100, 1, 0.01, 0.2, 500, "call", american=True, q=0.08
    )

    assert american > european


def test_crr_parameters():
    u, d, p = crr_parameters(1, 0.05, 0.2, 1)

    assert u * d == pytest.approx(1)
    assert 0 < p < 1
    # The risk-neutral expected growth is the risk-free growth
    assert p * u + (1 - p) * d == pytest.approx(1.05127, abs=1e-5)


def test_arbitrage_tree_is_rejected():
    # One step with exp(r * dt) = 1.65 above u = exp(0.1)
    with pytest.raises(ValueError, match="No-arbitrage"):
        binomial_price(100, 100, 1, 0.5, 0.1, 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(T=0.0),
        dict(sigma=0.0),
        dict(n_steps=0),
        dict(S=-1.0),
        dict(option_type="straddle"),
    ],
)
def test_invalid_inputs_raise(kwargs):
    args = dict(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.2, n_steps=10) | kwargs

    with pytest.raises(ValueError):
        binomial_price(**args)
