"""Cox-Ross-Rubinstein binomial tree prices for European and American options."""

import math

import numpy as np
from numpy.typing import NDArray

from .black_scholes import OptionType, _sign


def crr_parameters(
    T: float, r: float, sigma: float, n_steps: int, q: float = 0.0
) -> tuple[float, float, float]:
    """Calculate the up factor, down factor and risk-neutral up probability.

    u = exp(sigma * sqrt(dt)), d = 1 / u
    p = (exp((r - q) * dt) - d) / (u - d)

    Args:
        T: Time to expiry in years, positive
        r: Continuously compounded risk-free rate
        sigma: Annualised volatility, positive
        n_steps: Number of time steps, at least 1
        q: Continuous dividend yield

    Returns:
        Tuple of (u, d, p)

    Raises:
        ValueError: If an input is out of range, or if d < exp((r - q) * dt) < u
            fails, which would allow arbitrage (use more steps)
    """
    if T <= 0:
        raise ValueError("T must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if n_steps < 1:
        raise ValueError("n_steps must be at least 1")

    dt = T / n_steps
    up = math.exp(sigma * math.sqrt(dt))
    down = 1 / up
    growth = math.exp((r - q) * dt)
    if not down < growth < up:
        raise ValueError(
            f"No-arbitrage condition d < exp((r - q) * dt) < u fails "
            f"(d={down:.6f}, growth={growth:.6f}, u={up:.6f}); use more steps"
        )
    return up, down, (growth - down) / (up - down)


def binomial_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    n_steps: int,
    option_type: OptionType = "call",
    american: bool = False,
    q: float = 0.0,
) -> float:
    """Price an option on a Cox-Ross-Rubinstein binomial tree.

    Works backwards from the payoffs at expiry, discounting the risk-neutral
    expected value at each node. For an American option each node is worth
    the larger of that value and the value of exercising there.

    The European price converges to the Black-Scholes price as n_steps grows,
    with an error of order 1 / n_steps.

    Args:
        S: Current stock price, not negative
        K: Strike price, not negative
        T: Time to expiry in years, positive
        r: Continuously compounded risk-free rate
        sigma: Annualised volatility, positive
        n_steps: Number of time steps, at least 1
        option_type: "call" or "put"
        american: True to allow exercise at any node
        q: Continuous dividend yield

    Returns:
        Option price

    Raises:
        ValueError: If an input is out of range; see crr_parameters
    """
    sign = _sign(option_type)
    if S < 0 or K < 0:
        raise ValueError("S and K must not be negative")
    up, down, p = crr_parameters(T, r, sigma, n_steps, q)
    discount = math.exp(-r * T / n_steps)

    def node_prices(step: int) -> NDArray[np.float64]:
        """Stock prices after `step` steps, from all up moves to all down moves."""
        downs = np.arange(step + 1)
        # Computed from S each time rather than stepped back by d, so that
        # rounding does not build up (the root is then exactly S)
        prices: NDArray[np.float64] = S * up ** (step - downs) * down**downs
        return prices

    values = np.maximum(sign * (node_prices(n_steps) - K), 0.0)

    for step in range(n_steps - 1, -1, -1):
        values = discount * (p * values[:-1] + (1 - p) * values[1:])
        if american:
            values = np.maximum(values, sign * (node_prices(step) - K))

    return float(values[0])
