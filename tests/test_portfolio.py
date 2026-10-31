"""Unit tests for Modern Portfolio Theory and CAPM calculations."""

import numpy as np
import pytest

from quant_finance.portfolio.capm import capm_expected_return, jensens_alpha
from quant_finance.portfolio.mpt import (
    covariance_from_correlation,
    portfolio_return,
    portfolio_variance,
    two_asset_frontier,
    two_asset_min_variance_weight,
)


class TestPortfolioMoments:
    """Tests for portfolio return, variance and covariance."""

    def test_return_is_the_weighted_average(self):
        assert portfolio_return([0.25, 0.75], [0.08, 0.12]) == pytest.approx(0.11)

    def test_covariance_from_correlation(self):
        cov = covariance_from_correlation([0.1, 0.2], [[1.0, 0.5], [0.5, 1.0]])
        np.testing.assert_allclose(cov, [[0.01, 0.01], [0.01, 0.04]])

    def test_variance_matches_the_expanded_two_asset_formula(self):
        w1, w2, s1, s2, rho = 0.3, 0.7, 0.15, 0.25, 0.4
        cov = covariance_from_correlation([s1, s2], [[1.0, rho], [rho, 1.0]])
        expected = w1**2 * s1**2 + w2**2 * s2**2 + 2 * w1 * w2 * s1 * s2 * rho
        assert portfolio_variance([w1, w2], cov) == pytest.approx(expected)

    def test_variance_matches_matrix_multiplication(self):
        w = np.array([0.5, 0.3, 0.2])
        vols = np.array([0.1, 0.2, 0.3])
        corr = np.array([[1.0, 0.2, 0.3], [0.2, 1.0, 0.4], [0.3, 0.4, 1.0]])
        cov = covariance_from_correlation(vols, corr)
        assert portfolio_variance(w, cov) == pytest.approx(w @ cov @ w)

    def test_batches_of_weights_match_single_portfolios(self):
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        batch = np.array([[0.2, 0.8], [0.6, 0.4]])
        expected = [portfolio_variance(w, cov) for w in batch]
        np.testing.assert_allclose(portfolio_variance(batch, cov), expected)


class TestTwoAssetFrontier:
    """Tests for two-asset portfolio combinations."""

    def test_end_points_are_the_individual_assets(self):
        returns, risks = two_asset_frontier([1.0, 0.0], 0.08, 0.12, 0.15, 0.25, 0.3)
        np.testing.assert_allclose(returns, [0.08, 0.12])
        np.testing.assert_allclose(risks, [0.15, 0.25])

    def test_perfect_correlation_makes_risk_linear(self):
        _, risk = two_asset_frontier(0.5, 0.08, 0.12, 0.1, 0.3, 1.0)
        assert risk == pytest.approx(0.2)

    def test_perfect_negative_correlation_can_remove_risk(self):
        weight = two_asset_min_variance_weight(0.1, 0.3, -1.0)
        _, risk = two_asset_frontier(weight, 0.08, 0.12, 0.1, 0.3, -1.0)
        assert risk == pytest.approx(0.0, abs=1e-7)
        assert not np.isnan(risk)


class TestMinVarianceWeight:
    """Tests for the two-asset minimum variance portfolio."""

    @pytest.mark.parametrize(
        "sigma1, sigma2, rho",
        [(0.15, 0.25, 0.3), (0.2, 0.2, 0.0), (0.3, 0.1, -0.5), (0.18, 0.22, -0.9)],
    )
    def test_matches_a_grid_search(self, sigma1, sigma2, rho):
        grid = np.linspace(0, 1, 100_001)
        _, risks = two_asset_frontier(grid, 0.0, 0.0, sigma1, sigma2, rho)
        weight = two_asset_min_variance_weight(sigma1, sigma2, rho)
        assert weight == pytest.approx(grid[np.argmin(risks)], abs=1e-4)

    def test_is_clipped_when_the_optimum_requires_short_selling(self):
        # The unconstrained optimum is negative for a much riskier, correlated asset 1
        assert two_asset_min_variance_weight(0.5, 0.1, 0.9) == 0.0
        assert two_asset_min_variance_weight(0.1, 0.5, 0.9) == 1.0

    def test_identical_perfectly_correlated_assets_split_evenly(self):
        assert two_asset_min_variance_weight(0.2, 0.2, 1.0) == 0.5


class TestCapm:
    """Tests for CAPM expected return and alpha."""

    def test_beta_of_zero_earns_the_risk_free_rate(self):
        assert capm_expected_return(0.0, 3.0, 9.0) == 3.0

    def test_beta_of_one_earns_the_market_return(self):
        assert capm_expected_return(1.0, 3.0, 9.0) == 9.0

    def test_known_value(self):
        assert capm_expected_return(1.5, 3.0, 9.0) == pytest.approx(12.0)

    def test_negative_beta_earns_less_than_the_risk_free_rate(self):
        assert capm_expected_return(-0.5, 3.0, 9.0) == pytest.approx(0.0)

    def test_accepts_arrays(self):
        np.testing.assert_allclose(
            capm_expected_return(np.array([0.0, 1.0]), 3.0, 9.0), [3.0, 9.0]
        )

    def test_alpha_is_zero_on_the_security_market_line(self):
        assert jensens_alpha(12.0, 1.5, 3.0, 9.0) == pytest.approx(0.0)

    def test_alpha_is_the_excess_over_capm(self):
        assert jensens_alpha(14.0, 1.5, 3.0, 9.0) == pytest.approx(2.0)
