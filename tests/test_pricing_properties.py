"""Property-based tests of the pricing maths.

The example-based tests check chosen inputs. These check relationships that
must hold for every valid input, whatever the model or parameters, using
Hypothesis to search for counterexamples:

- no-arbitrage bounds, monotonicity and convexity of European prices;
- exact identities: put-call parity, put-call symmetry, scaling;
- the Black-Scholes PDE, satisfied by the library's own Greeks;
- the risk-neutral density implied by the prices (Breeden-Litzenberger);
- implied volatility recovering the volatility used to price;
- binomial trees: exact parity on the tree, American >= European >= 0.

Tolerances are relative to the size of the prices involved, because the
inputs span several orders of magnitude.
"""

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.stats import norm

from quant_finance.pricing.binomial import binomial_price
from quant_finance.pricing.black_scholes import (
    black_scholes_delta,
    black_scholes_gamma,
    black_scholes_price,
    black_scholes_theta,
    black_scholes_vega,
    implied_volatility,
)

PROPERTY = settings(max_examples=300, deadline=None)

spots = st.floats(1.0, 1_000.0)
moneyness = st.floats(0.25, 4.0)  # K / S
expiries = st.floats(0.01, 5.0)
rates = st.floats(-0.02, 0.15)
dividends = st.floats(0.0, 0.10)
vols = st.floats(0.01, 2.0)
option_types = st.sampled_from(["call", "put"])


@st.composite
def options(draw):
    """(S, K, T, r, sigma, q) for a live European option."""
    S = draw(spots)
    return (
        S,
        S * draw(moneyness),
        draw(expiries),
        draw(rates),
        draw(vols),
        draw(dividends),
    )


def price(S, K, T, r, sigma, q, option_type="call"):
    return float(black_scholes_price(S, K, T, r, sigma, q, option_type))


def tolerance(S, K):
    """Absolute tolerance scaled to the prices: about 1e-9 of the larger of S, K."""
    return 1e-9 * max(S, K)


# --- No-arbitrage bounds ----------------------------------------------------


@PROPERTY
@given(options())
def test_prices_lie_within_no_arbitrage_bounds(params):
    S, K, T, r, sigma, q = params
    forward_spot, forward_strike = S * math.exp(-q * T), K * math.exp(-r * T)
    call, put = price(*params, "call"), price(*params, "put")
    tol = tolerance(S, K)

    assert max(forward_spot - forward_strike, 0) - tol <= call <= forward_spot + tol
    assert max(forward_strike - forward_spot, 0) - tol <= put <= forward_strike + tol


# --- Exact identities -------------------------------------------------------


@PROPERTY
@given(options())
def test_put_call_parity(params):
    S, K, T, r, sigma, q = params
    call, put = price(*params, "call"), price(*params, "put")
    assert call - put == pytest.approx(
        S * math.exp(-q * T) - K * math.exp(-r * T), abs=tolerance(S, K)
    )


@PROPERTY
@given(options())
def test_put_call_symmetry(params):
    """C(S, K, r, q) = P(K, S, q, r): swapping spot with strike and r with q.

    McDonald and Schroder (1998); it holds exactly in Black-Scholes-Merton.
    """
    S, K, T, r, sigma, q = params
    assert price(S, K, T, r, sigma, q, "call") == pytest.approx(
        price(K, S, T, q, sigma, r, "put"), rel=1e-9, abs=tolerance(S, K)
    )


@PROPERTY
@given(options(), st.floats(0.01, 100.0), option_types)
def test_prices_scale_with_spot_and_strike(params, scale, option_type):
    """Prices are homogeneous of degree one in (S, K): only moneyness matters."""
    S, K, T, r, sigma, q = params
    scaled = price(scale * S, scale * K, T, r, sigma, q, option_type)
    assert scaled == pytest.approx(
        scale * price(*params, option_type), rel=1e-9, abs=scale * tolerance(S, K)
    )


# --- Monotonicity and convexity ---------------------------------------------


@PROPERTY
@given(options(), option_types)
def test_prices_rise_with_volatility(params, option_type):
    S, K, T, r, sigma, q = params
    lower = price(S, K, T, r, sigma, q, option_type)
    higher = price(S, K, T, r, sigma * 1.01, q, option_type)
    assert higher >= lower - tolerance(S, K)


@PROPERTY
@given(options())
def test_calls_fall_and_puts_rise_with_strike(params):
    S, K, T, r, sigma, q = params
    tol = tolerance(S, K)
    assert price(S, K * 1.01, T, r, sigma, q, "call") <= price(*params, "call") + tol
    assert price(S, K * 1.01, T, r, sigma, q, "put") >= price(*params, "put") - tol


@PROPERTY
@given(options(), option_types)
def test_prices_are_convex_in_strike(params, option_type):
    S, K, T, r, sigma, q = params
    h = 0.01 * K
    left = price(S, K - h, T, r, sigma, q, option_type)
    middle = price(S, K, T, r, sigma, q, option_type)
    right = price(S, K + h, T, r, sigma, q, option_type)
    assert left + right - 2 * middle >= -4 * tolerance(S, K)


@PROPERTY
@given(options(), option_types)
def test_prices_are_convex_in_spot(params, option_type):
    S, K, T, r, sigma, q = params
    h = 0.01 * S
    left = price(S - h, K, T, r, sigma, q, option_type)
    middle = price(S, K, T, r, sigma, q, option_type)
    right = price(S + h, K, T, r, sigma, q, option_type)
    assert left + right - 2 * middle >= -4 * tolerance(S, K)


@PROPERTY
@given(options())
def test_delta_lies_within_its_bounds(params):
    S, K, T, r, sigma, q = params
    carry = math.exp(-q * T)
    call_delta = float(black_scholes_delta(*params, "call"))
    put_delta = float(black_scholes_delta(*params, "put"))
    assert 0.0 <= call_delta <= carry
    assert -carry <= put_delta <= 0.0
    assert call_delta - put_delta == pytest.approx(carry, abs=1e-12)


# --- The Black-Scholes PDE --------------------------------------------------


@PROPERTY
@given(options(), option_types)
def test_greeks_satisfy_the_black_scholes_pde(params, option_type):
    """Theta + (r - q) S Delta + 1/2 sigma^2 S^2 Gamma = r V."""
    S, K, T, r, sigma, q = params
    value = price(*params, option_type)
    theta = float(black_scholes_theta(*params, option_type))
    delta = float(black_scholes_delta(*params, option_type))
    gamma = float(black_scholes_gamma(*params))
    lhs = theta + (r - q) * S * delta + 0.5 * sigma**2 * S**2 * gamma
    # Each term can be large and they nearly cancel, so scale by their size.
    scale = abs(theta) + abs((r - q) * S * delta) + 0.5 * sigma**2 * S**2 * gamma
    assert lhs == pytest.approx(r * value, abs=1e-9 * max(scale, 1.0))


# --- Risk-neutral density (Breeden-Litzenberger) ----------------------------


@pytest.mark.parametrize("S", [80.0, 100.0, 125.0])
@pytest.mark.parametrize("K", [70.0, 100.0, 140.0])
@pytest.mark.parametrize(
    "T, r, sigma, q", [(0.25, 0.03, 0.2, 0.0), (2.0, 0.05, 0.4, 0.02)]
)
def test_second_strike_derivative_is_the_lognormal_density(S, K, T, r, sigma, q):
    """e^{rT} d2C/dK2 is the risk-neutral density of S_T at K.

    Under Black-Scholes-Merton, ln S_T ~ N(ln S + (r - q - sigma^2/2) T, sigma^2 T),
    so the density is n(d2) / (K sigma sqrt(T)). This checks that the prices
    imply the distribution the model assumes, not just a convex function.
    """
    h = 1e-3 * K
    second = (
        price(S, K + h, T, r, sigma, q)
        - 2 * price(S, K, T, r, sigma, q)
        + price(S, K - h, T, r, sigma, q)
    ) / h**2
    d2 = (math.log(S / K) + (r - q - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    density = norm.pdf(d2) / (K * sigma * math.sqrt(T))
    # The second difference loses about eps * C / h^2 to rounding, which
    # matters only far in the tails, where the density is below 1e-8.
    assert math.exp(r * T) * second == pytest.approx(density, rel=1e-4, abs=1e-10)


def test_implied_density_integrates_to_one():
    """The density from the call prices is a probability distribution with the forward as mean."""
    S, T, r, sigma, q = 100.0, 1.0, 0.05, 0.3, 0.02
    strikes = np.linspace(1.0, 600.0, 60_001)
    calls = black_scholes_price(S, strikes, T, r, sigma, q)
    density = math.exp(r * T) * np.gradient(np.gradient(calls, strikes), strikes)
    assert np.trapezoid(density, strikes) == pytest.approx(1.0, abs=1e-4)
    assert np.trapezoid(strikes * density, strikes) == pytest.approx(
        S * math.exp((r - q) * T), rel=1e-4
    )


# --- Implied volatility -----------------------------------------------------


@PROPERTY
@given(options(), option_types)
def test_implied_volatility_recovers_sigma(params, option_type):
    S, K, T, r, sigma, q = params
    # Where vega is negligible the price does not pin down sigma; the solver
    # rightly returns NaN there (tested in test_implied_volatility.py).
    assume(float(black_scholes_vega(*params)) > 1e-4 * S)
    target = price(*params, option_type)
    implied = float(implied_volatility(target, S, K, T, r, q, option_type))
    assert implied == pytest.approx(sigma, rel=1e-6)


# --- Binomial trees ---------------------------------------------------------


@st.composite
def tree_options(draw):
    """Inputs for which a 200-step CRR tree is arbitrage-free."""
    S = draw(st.floats(10.0, 500.0))
    K = S * draw(st.floats(0.5, 2.0))
    T = draw(st.floats(0.05, 3.0))
    r = draw(st.floats(0.0, 0.12))
    sigma = draw(st.floats(0.05, 1.0))
    q = draw(st.floats(0.0, 0.08))
    dt = T / 200
    assume(
        math.exp(-sigma * math.sqrt(dt))
        < math.exp((r - q) * dt)
        < math.exp(sigma * math.sqrt(dt))
    )
    return S, K, T, r, sigma, q


@settings(max_examples=100, deadline=None)
@given(tree_options())
def test_put_call_parity_holds_exactly_on_the_tree(params):
    """The tree's risk-neutral measure prices the forward exactly, so parity is exact."""
    S, K, T, r, sigma, q = params
    call = binomial_price(S, K, T, r, sigma, 200, "call", q=q)
    put = binomial_price(S, K, T, r, sigma, 200, "put", q=q)
    assert call - put == pytest.approx(
        S * math.exp(-q * T) - K * math.exp(-r * T), abs=1e-9 * max(S, K)
    )


@settings(max_examples=100, deadline=None)
@given(tree_options(), option_types)
def test_american_is_worth_at_least_european_and_intrinsic(params, option_type):
    S, K, T, r, sigma, q = params
    european = binomial_price(S, K, T, r, sigma, 200, option_type, q=q)
    american = binomial_price(S, K, T, r, sigma, 200, option_type, american=True, q=q)
    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    tol = 1e-9 * max(S, K)
    assert american >= european - tol
    assert american >= intrinsic - tol
    assert european >= -tol


@settings(max_examples=100, deadline=None)
@given(tree_options())
def test_american_put_is_bounded_by_the_strike(params):
    S, K, T, r, sigma, q = params
    assert binomial_price(S, K, T, r, sigma, 200, "put", american=True, q=q) <= K + 1e-9
