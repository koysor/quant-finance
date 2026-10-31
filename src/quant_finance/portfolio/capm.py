"""Capital Asset Pricing Model calculations."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def capm_expected_return(
    beta: ArrayLike, risk_free_rate: float, market_return: float
) -> NDArray[np.float64]:
    """Calculate expected return under CAPM.

    E(R_i) = R_f + beta_i * (R_m - R_f)

    Args:
        beta: Asset beta(s)
        risk_free_rate: Risk-free rate
        market_return: Expected market return, in the same units as the risk-free rate

    Returns:
        Expected return(s), in the same units as the inputs
    """
    return risk_free_rate + np.asarray(beta, dtype=np.float64) * (
        market_return - risk_free_rate
    )


def jensens_alpha(
    actual_return: ArrayLike,
    beta: ArrayLike,
    risk_free_rate: float,
    market_return: float,
) -> NDArray[np.float64]:
    """Calculate Jensen's alpha: actual return less the CAPM expected return.

    alpha_i = R_i - E(R_i)

    Args:
        actual_return: Actual asset return(s)
        beta: Asset beta(s)
        risk_free_rate: Risk-free rate
        market_return: Expected market return, in the same units as the risk-free rate

    Returns:
        Alpha(s), in the same units as the inputs
    """
    expected = capm_expected_return(beta, risk_free_rate, market_return)
    return np.asarray(actual_return, dtype=np.float64) - expected
