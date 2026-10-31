"""Simulated paths of stochastic processes, shaped (n_paths, n_steps + 1)."""

import numpy as np
from numpy.typing import NDArray


def gbm_paths(
    S0: float,
    mu: float,
    sigma: float,
    T: float,
    n_steps: int,
    n_paths: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Simulate geometric Brownian motion using its exact discretisation.

    S(t + dt) = S(t) * exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)

    Args:
        S0: Initial price
        mu: Annual drift
        sigma: Annual volatility
        T: Time horizon in years
        n_steps: Number of time steps
        n_paths: Number of paths
        rng: Random number generator

    Returns:
        Simulated prices
    """
    dt = T / n_steps
    Z = rng.standard_normal((n_paths, n_steps))
    log_returns = np.zeros((n_paths, n_steps + 1))
    log_returns[:, 1:] = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    return S0 * np.exp(np.cumsum(log_returns, axis=1))


def wiener_paths(
    T: float, n_steps: int, n_paths: int, rng: np.random.Generator
) -> NDArray[np.float64]:
    """Simulate a standard Wiener process starting at zero.

    Args:
        T: Time horizon
        n_steps: Number of time steps
        n_paths: Number of paths
        rng: Random number generator

    Returns:
        Simulated values of W(t)
    """
    dt = T / n_steps
    # Draw independent N(0, dt) increments
    dW = rng.normal(0, np.sqrt(dt), (n_paths, n_steps))
    # Accumulate increments to form paths W(t)
    W = np.zeros((n_paths, n_steps + 1))
    W[:, 1:] = np.cumsum(dW, axis=1)
    return W


def random_walk_paths(
    initial_value: float,
    up_probability: float,
    n_steps: int,
    n_paths: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Simulate a random walk moving +1 or -1 at each step.

    It is a martingale when up_probability is 0.5, a sub-martingale above that
    and a super-martingale below it.

    Args:
        initial_value: Starting value
        up_probability: Probability of a +1 step
        n_steps: Number of time steps
        n_paths: Number of paths
        rng: Random number generator

    Returns:
        Simulated values
    """
    steps = rng.choice(
        [1, -1], size=(n_paths, n_steps), p=[up_probability, 1 - up_probability]
    )
    paths = np.full((n_paths, n_steps + 1), float(initial_value))
    paths[:, 1:] += np.cumsum(steps, axis=1)
    return paths
