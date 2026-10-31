"""Black-Scholes prices for European options on a non-dividend-paying stock."""

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import norm


def _price(
    S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike, sign: int
) -> NDArray[np.float64]:
    """Price a call (sign = 1) or put (sign = -1), broadcasting all inputs.

    When T or sigma is zero the terminal price is known, so the price is the
    discounted intrinsic value. This includes the payoff itself at expiry.
    """
    spot, strike, expiry, rate, vol = (
        np.asarray(value, dtype=np.float64) for value in (S, K, T, r, sigma)
    )
    time = np.maximum(expiry, 0.0)
    discounted_strike = strike * np.exp(-rate * time)
    total_vol = vol * np.sqrt(time)

    with np.errstate(divide="ignore", invalid="ignore"):
        d1 = (np.log(spot / strike) + (rate + 0.5 * vol**2) * time) / total_vol
    d2 = d1 - total_vol

    price = sign * (
        spot * norm.cdf(sign * d1) - discounted_strike * norm.cdf(sign * d2)
    )
    intrinsic = np.maximum(sign * (spot - discounted_strike), 0.0)
    return np.where(total_vol > 0, price, intrinsic)[()]


def black_scholes_call(
    S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike
) -> NDArray[np.float64]:
    """Calculate the Black-Scholes price of a European call.

    C = S * N(d1) - K * exp(-r * T) * N(d2)

    Args:
        S: Current stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years; values of zero or below are treated as expired
        r: Continuously compounded risk-free rate(s)
        sigma: Annualised volatility or volatilities, which must not be negative

    Returns:
        Call price(s), with the inputs broadcast against each other
    """
    return _price(S, K, T, r, sigma, sign=1)


def black_scholes_put(
    S: ArrayLike, K: ArrayLike, T: ArrayLike, r: ArrayLike, sigma: ArrayLike
) -> NDArray[np.float64]:
    """Calculate the Black-Scholes price of a European put.

    P = K * exp(-r * T) * N(-d2) - S * N(-d1)

    Args:
        S: Current stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years; values of zero or below are treated as expired
        r: Continuously compounded risk-free rate(s)
        sigma: Annualised volatility or volatilities, which must not be negative

    Returns:
        Put price(s), with the inputs broadcast against each other
    """
    return _price(S, K, T, r, sigma, sign=-1)
