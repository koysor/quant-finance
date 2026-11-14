"""Convergence and reference-value tests for the numerical methods.

- Reference values published in Haug (2007), independent of this library.
- The CRR binomial error shrinks at order 1/n.
- Monte Carlo prices from simulated GBM agree with Black-Scholes, and their
  error shrinks as 1 / sqrt(number of paths).
- Simulated paths have the properties their theory gives: the discounted price
  is a martingale, the Wiener process has quadratic variation T, and the GBM
  log returns are normal.

Every random test uses a fixed seed, so results are reproducible; thresholds
are set at four or more standard errors so a correct implementation passes for
almost any seed.
"""

import math

import numpy as np
import pytest
from scipy import stats

from quant_finance.pricing.binomial import binomial_price
from quant_finance.pricing.black_scholes import black_scholes_price
from quant_finance.stochastic.paths import gbm_paths, wiener_paths

# --- Independent reference values -------------------------------------------


@pytest.mark.parametrize(
    "S, K, T, r, sigma, q, option_type, expected",
    [
        # Haug (2007), The Complete Guide to Option Pricing Formulas, 2nd ed.,
        # section 1.1.1: Black-Scholes call.
        (60.0, 65.0, 0.25, 0.08, 0.30, 0.0, "call", 2.1334),
        # Haug (2007), section 1.1.4: Merton (1973) put on a stock index with
        # a continuous dividend yield.
        (100.0, 95.0, 0.5, 0.10, 0.20, 0.05, "put", 2.4648),
    ],
)
def test_haug_reference_values(S, K, T, r, sigma, q, option_type, expected):
    assert black_scholes_price(S, K, T, r, sigma, q, option_type) == pytest.approx(
        expected, abs=5e-5
    )


# --- Binomial convergence ---------------------------------------------------

STEPS = [25, 50, 100, 200, 400, 800, 1600]


def _tree_errors(S, K, option_type="call"):
    exact = float(black_scholes_price(S, K, 1.0, 0.05, 0.25, 0.0, option_type))
    return np.array(
        [
            abs(binomial_price(S, K, 1.0, 0.05, 0.25, n, option_type) - exact)
            for n in STEPS
        ]
    )


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_binomial_error_is_first_order_at_the_money(option_type):
    """At the money the error falls smoothly, with log-log slope -1."""
    errors = _tree_errors(100.0, 100.0, option_type)
    slope = np.polyfit(np.log(STEPS), np.log(errors), 1)[0]
    assert slope == pytest.approx(-1.0, abs=0.1)
    assert (np.diff(errors) < 0).all()


@pytest.mark.parametrize("S, K", [(100.0, 95.0), (100.0, 110.0), (90.0, 100.0)])
def test_binomial_error_is_bounded_by_c_over_n_away_from_the_money(S, K):
    """Away from the money the error oscillates, but n * error stays bounded.

    A method slower than first order would make n * error grow with n.
    """
    scaled = np.array(STEPS) * _tree_errors(S, K)
    early, late = scaled[: len(STEPS) // 2], scaled[len(STEPS) // 2 :]
    assert late.max() <= 1.5 * early.max()
    assert _tree_errors(S, K)[-1] < 2e-3


# --- Monte Carlo pricing ----------------------------------------------------


def _mc_call(n_paths, seed, S=100.0, K=105.0, T=1.0, r=0.05, sigma=0.2, q=0.01):
    """Risk-neutral Monte Carlo price of a European call and its standard error."""
    rng = np.random.default_rng(seed)
    terminal = gbm_paths(S, r - q, sigma, T, 1, n_paths, rng)[:, -1]
    payoffs = math.exp(-r * T) * np.maximum(terminal - K, 0.0)
    return payoffs.mean(), payoffs.std(ddof=1) / math.sqrt(n_paths)


def test_monte_carlo_price_matches_black_scholes():
    estimate, standard_error = _mc_call(400_000, seed=11)
    exact = float(black_scholes_price(100.0, 105.0, 1.0, 0.05, 0.2, 0.01))
    assert abs(estimate - exact) < 4 * standard_error
    assert standard_error < 0.03  # the test is sharp enough to catch real errors


def test_monte_carlo_error_shrinks_as_one_over_root_n():
    """Sixteen times the paths should cut the spread of estimates by four."""
    small = [_mc_call(1_000, seed)[0] for seed in range(200)]
    large = [_mc_call(16_000, seed)[0] for seed in range(200, 400)]
    ratio = np.std(small, ddof=1) / np.std(large, ddof=1)
    # With 200 estimates each, the ratio of standard deviations is within
    # about 10% of its true value; 4 * (1 +/- 0.25) leaves a wide margin.
    assert 3.0 < ratio < 5.0


def test_reported_standard_error_matches_the_spread_of_estimates():
    estimates, errors = zip(
        *(_mc_call(4_000, seed) for seed in range(200)), strict=True
    )
    assert np.std(estimates, ddof=1) == pytest.approx(np.mean(errors), rel=0.15)


# --- Properties of the simulated paths --------------------------------------


@pytest.mark.parametrize("step", [1, 25, 50])
def test_discounted_risk_neutral_price_is_a_martingale(step):
    """E[exp(-(r - q) t) S_t] = S_0 at every time t, not just at expiry."""
    r, q, T, n_steps = 0.05, 0.02, 1.0, 50
    paths = gbm_paths(100.0, r - q, 0.3, T, n_steps, 200_000, np.random.default_rng(5))
    t = step * T / n_steps
    discounted = math.exp(-(r - q) * t) * paths[:, step]
    standard_error = discounted.std(ddof=1) / math.sqrt(discounted.size)
    assert abs(discounted.mean() - 100.0) < 4 * standard_error


def test_gbm_log_returns_are_normal():
    """The exact scheme gives normal log returns whatever the step size."""
    mu, sigma, T = 0.08, 0.35, 2.0
    paths = gbm_paths(50.0, mu, sigma, T, 3, 20_000, np.random.default_rng(9))
    log_returns = np.log(paths[:, -1] / 50.0)
    mean, sd = (mu - 0.5 * sigma**2) * T, sigma * math.sqrt(T)
    assert stats.kstest(log_returns, stats.norm(mean, sd).cdf).pvalue > 1e-3


def test_gbm_variance_matches_theory():
    S0, mu, sigma, T = 100.0, 0.05, 0.25, 1.0
    final = gbm_paths(S0, mu, sigma, T, 1, 400_000, np.random.default_rng(3))[:, -1]
    expected = S0**2 * math.exp(2 * mu * T) * (math.exp(sigma**2 * T) - 1)
    assert final.var(ddof=1) == pytest.approx(expected, rel=0.02)


def test_wiener_quadratic_variation_is_t():
    """The sum of squared increments converges to T as the grid gets finer.

    For n steps its variance is 2 T^2 / n, so with n = 100,000 it is within
    about 0.0045 of T (one standard deviation) on every path.
    """
    T = 1.5
    paths = wiener_paths(T, 100_000, 20, np.random.default_rng(2))
    quadratic_variation = (np.diff(paths, axis=1) ** 2).sum(axis=1)
    sd = math.sqrt(2 * T**2 / 100_000)
    assert np.abs(quadratic_variation - T).max() < 5 * sd
