"""Modern Portfolio Theory calculations."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def portfolio_return(weights: ArrayLike, returns: ArrayLike) -> NDArray[np.float64]:
    """Calculate expected portfolio return.

    R_p = w^T * R

    Args:
        weights: Asset weights, or an array of them with assets on the last axis
        returns: Expected asset returns

    Returns:
        Expected portfolio return(s)
    """
    return np.asarray(weights, dtype=np.float64) @ np.asarray(returns, dtype=np.float64)


def portfolio_variance(weights: ArrayLike, cov: ArrayLike) -> NDArray[np.float64]:
    """Calculate portfolio variance.

    sigma_p^2 = w^T * Sigma * w

    Args:
        weights: Asset weights, or an array of them with assets on the last axis
        cov: Covariance matrix of asset returns

    Returns:
        Portfolio variance(s)
    """
    w = np.asarray(weights, dtype=np.float64)
    variance: NDArray[np.float64] = np.einsum(
        "...i,ij,...j", w, np.asarray(cov, dtype=np.float64), w
    )
    return variance


def covariance_from_correlation(
    vols: ArrayLike, corr: ArrayLike
) -> NDArray[np.float64]:
    """Build a covariance matrix from volatilities and correlations.

    Cov(i, j) = rho_ij * sigma_i * sigma_j

    Args:
        vols: Asset volatilities
        corr: Correlation matrix

    Returns:
        Covariance matrix
    """
    sigma = np.asarray(vols, dtype=np.float64)
    return np.asarray(corr, dtype=np.float64) * np.outer(sigma, sigma)


def two_asset_frontier(
    w1: ArrayLike, r1: float, r2: float, sigma1: float, sigma2: float, rho: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Calculate return and risk of two-asset portfolios.

    Args:
        w1: Weight(s) in asset 1, with the remainder in asset 2
        r1: Expected return of asset 1
        r2: Expected return of asset 2
        sigma1: Volatility of asset 1
        sigma2: Volatility of asset 2
        rho: Correlation between the assets

    Returns:
        Tuple of (portfolio returns, portfolio volatilities)
    """
    w = np.asarray(w1, dtype=np.float64)
    weights = np.stack([w, 1 - w], axis=-1)
    cov = covariance_from_correlation([sigma1, sigma2], [[1.0, rho], [rho, 1.0]])
    # Rounding can leave a tiny negative variance when rho is -1
    variance = np.maximum(portfolio_variance(weights, cov), 0.0)
    return portfolio_return(weights, [r1, r2]), np.sqrt(variance)


def two_asset_min_variance_weight(sigma1: float, sigma2: float, rho: float) -> float:
    """Calculate the weight in asset 1 of the minimum variance portfolio.

    w1 = (sigma2^2 - rho * sigma1 * sigma2)
         / (sigma1^2 + sigma2^2 - 2 * rho * sigma1 * sigma2)

    The weight is clipped to [0, 1], so short selling is not allowed.

    Args:
        sigma1: Volatility of asset 1
        sigma2: Volatility of asset 2
        rho: Correlation between the assets

    Returns:
        Weight in asset 1; 0.5 if every portfolio has the same variance
    """
    denominator = sigma1**2 + sigma2**2 - 2 * sigma1 * sigma2 * rho
    if denominator == 0:
        return 0.5
    return float(np.clip((sigma2**2 - sigma1 * sigma2 * rho) / denominator, 0, 1))
