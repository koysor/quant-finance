"""Unit tests for the Cox-Ross-Rubinstein binomial pricer."""

import math

import numpy as np
import pytest
from scipy.stats import norm

from quant_finance.pricing.binomial import (
    binomial_lattice,
    binomial_price,
    binomial_price_closed_form,
    crr_parameters,
    digital_call_payoff,
    terminal_distribution,
)
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


digital_call = digital_call_payoff(100.0)


def power_call(prices):
    return np.maximum(prices**2 - 100.0**2, 0.0)


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("american", [False, True])
@pytest.mark.parametrize("q", [0.0, 0.04])
def test_lattice_root_matches_binomial_price(option_type, american, q):
    args = (95.0, 100.0, 0.75, 0.05, 0.3, 40, option_type)
    lattice = binomial_lattice(*args, american=american, q=q)

    assert lattice.value[0][0] == pytest.approx(
        binomial_price(*args, american=american, q=q), rel=1e-12
    )


def test_lattice_shape_and_root():
    lattice = binomial_lattice(100.0, 100.0, 1.0, 0.05, 0.2, 6)

    assert [len(level) for level in lattice.stock] == list(range(1, 8))
    assert [len(level) for level in lattice.delta] == list(range(1, 7))
    assert lattice.stock[0][0] == 100.0
    # Node 0 is the all-up node
    assert lattice.stock[6][0] == pytest.approx(100.0 * lattice.up**6)


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("payoff", [None, digital_call, power_call])
def test_closed_form_equals_backward_induction(option_type, payoff):
    args = (105.0, 100.0, 1.0, 0.04, 0.25, 25, option_type)

    induction = binomial_lattice(*args, q=0.01, payoff=payoff).value[0][0]
    closed = binomial_price_closed_form(*args, q=0.01, payoff=payoff)

    assert closed == pytest.approx(induction, rel=1e-10)


def assert_lattice_replicates(lattice, r, q):
    """delta shares (dividends reinvested) plus the bond reach both successors."""
    growth = math.exp(r * lattice.dt)
    share_growth = math.exp(q * lattice.dt)
    scale = max(float(np.max(level)) for level in lattice.value) + 1.0

    for step in range(len(lattice.delta)):
        for successor, offset in (
            (lattice.stock[step + 1][:-1], 0),
            (lattice.stock[step + 1][1:], 1),
        ):
            replicated = (
                lattice.delta[step] * share_growth * successor
                + lattice.bond[step] * growth
            )
            target = lattice.value[step + 1][offset : offset + step + 1]
            np.testing.assert_allclose(replicated, target, rtol=0, atol=1e-10 * scale)


@pytest.mark.parametrize("american", [False, True])
@pytest.mark.parametrize("q", [0.0, 0.06])
def test_delta_and_bond_replicate_both_successors(american, q):
    r = 0.05
    lattice = binomial_lattice(
        90.0, 100.0, 1.0, r, 0.3, 8, "put", american=american, q=q
    )

    assert_lattice_replicates(lattice, r, q)


def test_hedged_portfolio_earns_the_risk_free_rate_with_dividends():
    # Long the option, short delta shares: the short owes the dividends, so
    # Pi = V - delta S grows to V+ - exp(q dt) delta S+ in the up state
    r, q = 0.05, 0.06
    lattice = binomial_lattice(100.0, 100.0, 1.0, r, 0.2, 4, "call", q=q)
    v_up, v_down = lattice.value[1]
    s_up, s_down = lattice.stock[1]
    shares_owed = lattice.delta[0][0] * math.exp(q * lattice.dt)
    pi_now = lattice.value[0][0] - lattice.delta[0][0] * 100.0

    pi_up = v_up - shares_owed * s_up
    assert pi_up == pytest.approx(v_down - shares_owed * s_down)
    assert pi_now * math.exp(r * lattice.dt) == pytest.approx(pi_up)


def test_root_delta_matches_one_step_formula():
    lattice = binomial_lattice(100.0, 100.0, 1.0, 0.05, 0.2, 4)
    v_up, v_down = lattice.value[1]
    s_up, s_down = lattice.stock[1]

    assert lattice.delta[0][0] == pytest.approx((v_up - v_down) / (s_up - s_down))


def test_deep_in_the_money_american_put_exercises_early():
    lattice = binomial_lattice(70.0, 100.0, 1.0, 0.08, 0.2, 20, "put", american=True)

    assert any(level.any() for level in lattice.exercise)
    # Wherever it exercises, the value is the intrinsic value
    for stock, value, exercise in zip(lattice.stock, lattice.value, lattice.exercise):
        np.testing.assert_allclose(value[exercise], 100.0 - stock[exercise])


def test_american_call_without_dividends_has_no_exercise_nodes():
    lattice = binomial_lattice(120.0, 100.0, 1.0, 0.05, 0.2, 20, "call", american=True)

    assert not any(level.any() for level in lattice.exercise)


def test_european_lattice_has_no_exercise_nodes():
    lattice = binomial_lattice(70.0, 100.0, 1.0, 0.08, 0.2, 20, "put")

    assert not any(level.any() for level in lattice.exercise)


@pytest.mark.parametrize("n_steps", [1, 7, 200])
def test_terminal_distribution_is_risk_neutral(n_steps):
    S, T, r, q = 100.0, 2.0, 0.05, 0.02
    prices, probabilities = terminal_distribution(S, T, r, 0.3, n_steps, q)

    assert len(prices) == n_steps + 1
    assert probabilities.sum() == pytest.approx(1.0)
    # Under the risk-neutral measure the stock grows at r - q
    assert np.sum(probabilities * prices) == pytest.approx(S * math.exp((r - q) * T))


def test_lattice_and_closed_form_reject_bad_inputs():
    with pytest.raises(ValueError):
        binomial_lattice(100.0, 100.0, 1.0, 0.05, 0.2, 5, "straddle")
    with pytest.raises(ValueError, match="No-arbitrage"):
        binomial_lattice(100.0, 100.0, 1.0, 0.5, 0.1, 1)
    with pytest.raises(ValueError):
        binomial_price_closed_form(-1.0, 100.0, 1.0, 0.05, 0.2, 5)


@pytest.mark.parametrize("n_steps", [4, 50, 200])
def test_node_on_the_strike_is_exactly_the_strike(n_steps):
    # With S = K and an even step count the middle terminal node is S u^0
    lattice = binomial_lattice(100.0, 100.0, 1.0, 0.05, 0.2, n_steps)
    prices, _ = terminal_distribution(100.0, 1.0, 0.05, 0.2, n_steps)

    assert lattice.stock[n_steps][n_steps // 2] == 100.0
    assert prices[n_steps // 2] == 100.0


def test_digital_payoff_pays_half_on_the_strike():
    payoff = digital_call_payoff(100.0)

    np.testing.assert_array_equal(
        payoff(np.array([99.0, 100.0, 100.0 * (1 + 1e-14), 101.0])),
        [0.0, 0.5, 0.5, 1.0],
    )


@pytest.mark.parametrize("n_steps", [50, 51, 200, 201])
def test_digital_with_a_node_on_the_strike_converges(n_steps):
    # Black-Scholes cash-or-nothing call, exp(-rT) N(d2). Paying 0 at the
    # strike node instead would miss by 0.053 at n = 50 and 0.027 at n = 200
    S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
    d2 = (math.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    exact = math.exp(-r * T) * norm.cdf(d2)

    price = binomial_price_closed_form(
        S, K, T, r, sigma, n_steps, payoff=digital_call_payoff(K)
    )

    assert price == pytest.approx(exact, abs=1e-3)
