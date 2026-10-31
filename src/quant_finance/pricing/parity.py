"""Put-call parity calculations for European options."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def parity_difference(
    C: ArrayLike,
    P: ArrayLike,
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate the gap between the two sides of put-call parity.

    difference = (C + K * exp(-r * T)) - (P + S * exp(-q * T))

    Args:
        C: Call price(s)
        P: Put price(s)
        S: Stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years
        r: Continuously compounded risk-free rate(s)
        q: Continuous dividend yield(s)

    Returns:
        Difference(s), which are zero when parity holds
    """
    return np.add(C, _discount(K, r, T)) - np.add(P, _discount(S, q, T))


def implied_call(
    P: ArrayLike,
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate the call price implied by put-call parity.

    C = P + S * exp(-q * T) - K * exp(-r * T)

    Args:
        P: Put price(s)
        S: Stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years
        r: Continuously compounded risk-free rate(s)
        q: Continuous dividend yield(s)

    Returns:
        Implied call price(s)
    """
    return np.add(P, _discount(S, q, T)) - _discount(K, r, T)


def implied_put(
    C: ArrayLike,
    S: ArrayLike,
    K: ArrayLike,
    T: ArrayLike,
    r: ArrayLike,
    q: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Calculate the put price implied by put-call parity.

    P = C + K * exp(-r * T) - S * exp(-q * T)

    Args:
        C: Call price(s)
        S: Stock price(s)
        K: Strike price(s)
        T: Time(s) to expiry in years
        r: Continuously compounded risk-free rate(s)
        q: Continuous dividend yield(s)

    Returns:
        Implied put price(s)
    """
    return np.add(C, _discount(K, r, T)) - _discount(S, q, T)


def _discount(value: ArrayLike, rate: ArrayLike, T: ArrayLike) -> NDArray[np.float64]:
    """Discount a value at a continuously compounded rate."""
    return np.asarray(value, dtype=np.float64) * np.exp(-np.multiply(rate, T))
