"""Model-free static arbitrage checks on option prices."""

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike


def static_arbitrage_violations(
    strikes: ArrayLike,
    prices: ArrayLike,
    option_type: Literal["call", "put"] = "call",
    tol: float = 1e-9,
) -> list[str]:
    """List the static arbitrage conditions broken by same-expiry option prices.

    For European options on one underlying with one expiry, no-arbitrage
    requires, whatever the model:

    - Prices are not negative.
    - Calls get cheaper as the strike rises; puts get dearer.
    - Between two strikes the price changes by no more than the strike gap,
      |P(K2) - P(K1)| <= K2 - K1 (the bound with discounting is tighter, so a
      breach of this one is always an arbitrage).
    - Prices are convex in the strike: the slope between neighbouring strikes
      never falls. Otherwise a butterfly would cost less than nothing.

    Args:
        strikes: Strike prices, in any order
        prices: Option prices, one per strike
        option_type: "call" or "put"
        tol: Price tolerance, for example for prices rounded to the penny

    Returns:
        A description of each violation; empty if the prices are consistent

    Raises:
        ValueError: If strikes and prices differ in length or option_type is unknown
    """
    if option_type not in ("call", "put"):
        raise ValueError(f"option_type must be 'call' or 'put', not {option_type!r}")
    K = np.asarray(strikes, dtype=np.float64).ravel()
    P = np.asarray(prices, dtype=np.float64).ravel()
    if K.shape != P.shape:
        raise ValueError("strikes and prices must have the same length")

    order = np.argsort(K, kind="stable")
    K, P = K[order], P[order]
    name = option_type
    violations: list[str] = []

    for k, p in zip(K, P):
        if p < -tol:
            violations.append(f"The {k:g} {name} has a negative price ({p:g}).")

    for (k1, p1), (k2, p2) in zip(zip(K, P), zip(K[1:], P[1:])):
        if k1 == k2:
            if abs(p1 - p2) > tol:
                violations.append(
                    f"Two {name}s with strike {k1:g} have different prices "
                    f"({p1:g} and {p2:g})."
                )
            continue
        worse_payoff_costs_more = p2 > p1 + tol if name == "call" else p1 > p2 + tol
        if worse_payoff_costs_more:
            dear, cheap = (k2, k1) if name == "call" else (k1, k2)
            violations.append(
                f"The {dear:g} {name} costs more than the {cheap:g} {name}, "
                f"but its payoff is never higher."
            )
        if abs(p2 - p1) > k2 - k1 + tol:
            violations.append(
                f"The {k1:g} and {k2:g} {name}s differ by {abs(p2 - p1):g}, more "
                f"than the strike gap of {k2 - k1:g}."
            )

    # Convexity: each middle price is at most the straight-line interpolation of
    # its neighbours (compared in price terms, so tol is a price tolerance)
    distinct = np.concatenate(([True], np.diff(K) > 0))
    K, P = K[distinct], P[distinct]
    for i in range(len(K) - 2):
        weight = (K[i + 2] - K[i + 1]) / (K[i + 2] - K[i])
        interpolated = weight * P[i] + (1 - weight) * P[i + 2]
        if P[i + 1] > interpolated + tol:
            violations.append(
                f"The {K[i]:g}/{K[i + 1]:g}/{K[i + 2]:g} {name} prices are not "
                f"convex in the strike, so a butterfly on them costs less than nothing."
            )

    return violations
