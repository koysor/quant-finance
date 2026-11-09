"""Black-Scholes(-Merton) prices, Greeks and implied volatility.

European options on a stock paying a continuous dividend yield q; with the
default q = 0 these are the original Black-Scholes formulae.

d1 = (ln(S / K) + (r - q + sigma^2 / 2) * T) / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)

Every function broadcasts its inputs against each other. When T or sigma is
zero the terminal price is known, so prices and Greeks are those of the
discounted intrinsic value. Times of zero or below are treated as expired.

Units of the Greeks:
    delta, gamma: per unit change in S
    vega: per unit change in sigma (1.00 = 100 vol points); divide by 100 for
        the change per vol point
    theta: per year, as the change in value as time passes (usually
        negative); divide by 365 for the change per calendar day
    rho: per unit change in r (1.00 = 100%); divide by 100 for the change
        per percentage point
"""

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq
from scipy.stats import norm

OptionType = Literal["call", "put"]


class _Inputs:
    """Validated, broadcast inputs and the quantities every formula uses."""

    def __init__(
        self,
        S: ArrayLike,
        K: ArrayLike,
        T: ArrayLike,
        r: ArrayLike,
        sigma: ArrayLike,
        q: ArrayLike,
    ) -> None:
        spot, strike, expiry, rate, vol, dividend = np.broadcast_arrays(
            *(np.asarray(value, dtype=np.float64) for value in (S, K, T, r, sigma, q))
        )
        if np.any(spot < 0) or np.any(strike < 0):
            raise ValueError("S and K must not be negative")
        if np.any(vol < 0):
            raise ValueError("sigma must not be negative")

        self.S, self.K, self.r, self.sigma, self.q = spot, strike, rate, vol, dividend
        self.T = np.maximum(expiry, 0.0)
        self.sqrt_T = np.sqrt(self.T)
        self.total_vol = vol * self.sqrt_T
        self.live = self.total_vol > 0
        self.discounted_spot = spot * np.exp(-dividend * self.T)
        self.discounted_strike = strike * np.exp(-rate * self.T)

        with np.errstate(divide="ignore", invalid="ignore"):
            log_moneyness = np.log(self.discounted_spot / self.discounted_strike)
            d1 = log_moneyness / self.total_vol + 0.5 * self.total_vol
        # With no volatility the option finishes in the money for certain or
        # not at all, so d1 and d2 go to plus or minus infinity (0 exactly at
        # the forward, where the payoff has a kink)
        certain = np.where(
            log_moneyness > 0, np.inf, np.where(log_moneyness < 0, -np.inf, 0.0)
        )
        self.d1 = np.where(self.live, d1, certain)
        self.d2 = np.where(self.live, self.d1 - self.total_vol, self.d1)
        self.pdf_d1 = np.where(self.live, norm.pdf(self.d1), 0.0)


def _sign(option_type: OptionType) -> int:
    if option_type == "call":
        return 1
    if option_type == "put":
        return -1
    raise ValueError(f"option_type must be 'call' or 'put', not {option_type!r}")


def _scalar_if_0d(value: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return a NumPy scalar for 0-d results, as the price functions do."""
    result: NDArray[np.float64] = np.asarray(value, dtype=np.float64)[()]
    return result


def black_scholes_price(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
    option_type: OptionType = "call",
) -> NDArray[np.float64]:
    """Calculate the Black-Scholes price of a European call or put.

    C = S * exp(-q * T) * N(d1) - K * exp(-r * T) * N(d2)
    P = K * exp(-r * T) * N(-d2) - S * exp(-q * T) * N(-d1)

    Args:
        S: Current stock price(s), not negative
        K: Strike price(s), not negative
        T: Time(s) to expiry in years; values of zero or below are treated as expired
        r: Continuously compounded risk-free rate(s)
        sigma: Annualised volatility or volatilities, not negative
        q: Continuous dividend yield(s)
        option_type: "call" or "put"

    Returns:
        Price(s), with the inputs broadcast against each other

    Raises:
        ValueError: If S, K or sigma is negative, or option_type is unknown
    """
    sign = _sign(option_type)
    x = _Inputs(S, K, T, r, sigma, q)
    with np.errstate(invalid="ignore"):
        price = sign * (
            x.discounted_spot * norm.cdf(sign * x.d1)
            - x.discounted_strike * norm.cdf(sign * x.d2)
        )
    intrinsic = np.maximum(sign * (x.discounted_spot - x.discounted_strike), 0.0)
    return _scalar_if_0d(np.where(x.live, price, intrinsic))


def black_scholes_call(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate the Black-Scholes price of a European call.

    C = S * exp(-q * T) * N(d1) - K * exp(-r * T) * N(d2)

    See black_scholes_price for the arguments.
    """
    return black_scholes_price(S, K, T, r, sigma, q, "call")


def black_scholes_put(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate the Black-Scholes price of a European put.

    P = K * exp(-r * T) * N(-d2) - S * exp(-q * T) * N(-d1)

    See black_scholes_price for the arguments.
    """
    return black_scholes_price(S, K, T, r, sigma, q, "put")


def black_scholes_delta(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
    option_type: OptionType = "call",
) -> NDArray[np.float64]:
    """Calculate delta, the change in option value per unit change in S.

    Call: exp(-q * T) * N(d1)
    Put: -exp(-q * T) * N(-d1)

    See black_scholes_price for the arguments.
    """
    sign = _sign(option_type)
    x = _Inputs(S, K, T, r, sigma, q)
    return _scalar_if_0d(sign * np.exp(-x.q * x.T) * norm.cdf(sign * x.d1))


def black_scholes_gamma(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate gamma, the change in delta per unit change in S.

    Gamma = exp(-q * T) * n(d1) / (S * sigma * sqrt(T)), the same for calls and puts

    See black_scholes_price for the arguments.
    """
    x = _Inputs(S, K, T, r, sigma, q)
    with np.errstate(divide="ignore", invalid="ignore"):
        gamma = np.exp(-x.q * x.T) * x.pdf_d1 / (x.S * x.total_vol)
    return _scalar_if_0d(np.where(x.live & (x.S > 0), gamma, 0.0))


def black_scholes_vega(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate vega, the change in option value per unit change in sigma.

    Vega = S * exp(-q * T) * n(d1) * sqrt(T), the same for calls and puts.
    It is per 1.00 of volatility: divide by 100 for the change per vol point.

    See black_scholes_price for the arguments.
    """
    x = _Inputs(S, K, T, r, sigma, q)
    return _scalar_if_0d(x.discounted_spot * x.pdf_d1 * x.sqrt_T)


def black_scholes_theta(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
    option_type: OptionType = "call",
) -> NDArray[np.float64]:
    """Calculate theta, the change in option value per year as time passes.

    Theta = -S * exp(-q * T) * n(d1) * sigma / (2 * sqrt(T))
            + sign * (q * S * exp(-q * T) * N(sign * d1)
                      - r * K * exp(-r * T) * N(sign * d2))

    where sign is 1 for a call and -1 for a put. Divide by 365 for the change
    per calendar day.

    See black_scholes_price for the arguments.
    """
    sign = _sign(option_type)
    x = _Inputs(S, K, T, r, sigma, q)
    with np.errstate(divide="ignore", invalid="ignore"):
        decay = np.where(
            x.live, -x.discounted_spot * x.pdf_d1 * x.sigma / (2 * x.sqrt_T), 0.0
        )
    carry = sign * (
        x.q * x.discounted_spot * norm.cdf(sign * x.d1)
        - x.r * x.discounted_strike * norm.cdf(sign * x.d2)
    )
    return _scalar_if_0d(decay + carry)


def black_scholes_rho(
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    sigma: ArrayLike,
    q: ArrayLike = 0.0,
    option_type: OptionType = "call",
) -> NDArray[np.float64]:
    """Calculate rho, the change in option value per unit change in r.

    Call: K * T * exp(-r * T) * N(d2)
    Put: -K * T * exp(-r * T) * N(-d2)

    It is per 1.00 of rate: divide by 100 for the change per percentage point.

    See black_scholes_price for the arguments.
    """
    sign = _sign(option_type)
    x = _Inputs(S, K, T, r, sigma, q)
    return _scalar_if_0d(sign * x.T * x.discounted_strike * norm.cdf(sign * x.d2))


def implied_volatility(
    price: ArrayLike,
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike = 0.0,
    option_type: OptionType = "call",
    *,
    lower: float = 1e-6,
    upper: float = 5.0,
    tol: float = 1e-10,
) -> NDArray[np.float64]:
    """Find the volatility at which the Black-Scholes price equals a given price.

    Solved with Brent's method on [lower, upper]. The price of a European
    option rises strictly with volatility, so the root is unique when it exists.

    A price that no volatility in (lower, upper) can produce gives NaN rather
    than an error, so a whole option chain can be solved at once. That includes
    prices at or below the no-arbitrage bound (the discounted intrinsic
    value), prices at or above the upper bound (S * exp(-q * T) for a call,
    K * exp(-r * T) for a put), and expired options. It also includes deep
    in-the-money options whose price cannot be told apart from the intrinsic
    value in floating point, because vega there is effectively zero.

    Args:
        price: Option price(s)
        S: Current stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years
        r: Continuously compounded risk-free rate(s)
        q: Continuous dividend yield(s)
        option_type: "call" or "put"
        lower: Lowest volatility searched
        upper: Highest volatility searched
        tol: Absolute tolerance on the volatility

    Returns:
        Implied volatility or volatilities, NaN where there is no solution

    Raises:
        ValueError: If option_type is unknown or S or K is negative
    """
    _sign(option_type)
    target, spot, strike, expiry, rate, dividend = np.broadcast_arrays(
        *(np.asarray(v, dtype=np.float64) for v in (price, S, K, T, r, q))
    )
    if np.any(spot < 0) or np.any(strike < 0):
        raise ValueError("S and K must not be negative")

    result = np.full(target.shape, np.nan)
    for index in np.ndindex(target.shape):
        args = (spot[index], strike[index], expiry[index], rate[index])

        def error(vol: float) -> float:
            model = black_scholes_price(*args, vol, dividend[index], option_type)
            return float(model) - float(target[index])

        if expiry[index] <= 0 or not np.isfinite(target[index]):
            continue
        # The price must lie strictly between the prices at the two bounds.
        # A price no higher than the lower bound's cannot identify a
        # volatility: deep in the money, vega is so small that the price at
        # any low volatility is the discounted intrinsic value to machine
        # precision.
        low, high = error(lower), error(upper)
        if low >= 0 or high <= 0:
            continue
        result[index] = brentq(error, lower, upper, xtol=tol)
    return _scalar_if_0d(result)
