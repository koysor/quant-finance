"""Property-based tests of the portfolio maths (MPT and CAPM)."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from quant_finance.portfolio.capm import capm_expected_return, jensens_alpha
from quant_finance.portfolio.mpt import (
    portfolio_variance,
    two_asset_frontier,
    two_asset_min_variance_weight,
)

PROPERTY = settings(max_examples=300, deadline=None)

vols = st.floats(0.01, 1.0)
correlations = st.floats(-1.0, 1.0)


@PROPERTY
@given(
    arrays(np.float64, (4, 4), elements=st.floats(-1.0, 1.0)),
    arrays(np.float64, 4, elements=st.floats(-2.0, 2.0)),
)
def test_variance_is_never_negative_for_a_valid_covariance(factor, weights):
    """Any covariance matrix is A A^T for some A, and w^T A A^T w = |A^T w|^2."""
    cov = factor @ factor.T
    variance = float(portfolio_variance(weights, cov))
    assert variance >= -1e-12
    assert variance == pytest.approx(float(np.sum((factor.T @ weights) ** 2)), abs=1e-9)


@PROPERTY
@given(st.floats(0.0, 1.0), vols, vols, correlations)
def test_diversification_never_adds_risk(w, sigma1, sigma2, rho):
    """Portfolio volatility is at most the weighted average of the volatilities."""
    _, risk = two_asset_frontier(w, 0.05, 0.08, sigma1, sigma2, rho)
    assert float(risk) <= w * sigma1 + (1 - w) * sigma2 + 1e-12


@PROPERTY
@given(st.floats(0.0, 1.0), vols, vols)
def test_perfect_correlation_gives_no_diversification(w, sigma1, sigma2):
    _, risk = two_asset_frontier(w, 0.05, 0.08, sigma1, sigma2, 1.0)
    assert float(risk) == pytest.approx(w * sigma1 + (1 - w) * sigma2, abs=1e-12)


@PROPERTY
@given(vols, vols, correlations)
def test_min_variance_weight_minimises_variance_over_long_only_weights(
    sigma1, sigma2, rho
):
    w_star = two_asset_min_variance_weight(sigma1, sigma2, rho)
    assert 0.0 <= w_star <= 1.0
    grid = np.linspace(0.0, 1.0, 2001)
    _, risk = two_asset_frontier(grid, 0.05, 0.08, sigma1, sigma2, rho)
    _, best = two_asset_frontier(w_star, 0.05, 0.08, sigma1, sigma2, rho)
    assert float(best) <= risk.min() + 1e-9


@PROPERTY
@given(st.floats(-0.02, 0.1), st.floats(-0.2, 0.3))
def test_capm_line_passes_through_risk_free_and_market(rf, rm):
    assert float(capm_expected_return(0.0, rf, rm)) == pytest.approx(rf)
    assert float(capm_expected_return(1.0, rf, rm)) == pytest.approx(rm)


@PROPERTY
@given(st.floats(-1.0, 3.0), st.floats(-0.02, 0.1), st.floats(-0.2, 0.3))
def test_an_asset_on_the_security_market_line_has_zero_alpha(beta, rf, rm):
    on_the_line = capm_expected_return(beta, rf, rm)
    assert float(jensens_alpha(on_the_line, beta, rf, rm)) == pytest.approx(
        0.0, abs=1e-12
    )
