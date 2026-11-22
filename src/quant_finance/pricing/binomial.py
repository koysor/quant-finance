"""Cox-Ross-Rubinstein binomial tree prices for European and American options."""

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import binom

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

    values = np.maximum(sign * (_node_prices(S, up, n_steps) - K), 0.0)

    for step in range(n_steps - 1, -1, -1):
        values = discount * (p * values[:-1] + (1 - p) * values[1:])
        if american:
            values = np.maximum(values, sign * (_node_prices(S, up, step) - K))

    return float(values[0])


Payoff = Callable[[NDArray[np.float64]], NDArray[np.float64]]
"""A payoff at expiry: maps stock prices to option values, elementwise."""


def digital_call_payoff(K: float) -> Payoff:
    """Cash-or-nothing call paying 1 above the strike, and 1/2 at it.

    A payoff that jumps at K needs a convention for a node that lands on K,
    which on a CRR tree happens whenever K = S and the step count is even.
    Paying 0 or 1 there biases the price by about half that node's
    probability, which shrinks only like 1/sqrt(n); paying the midpoint 1/2
    removes most of the bias. Prices within a relative 1e-12 of K count as
    on it.

    Args:
        K: Strike price

    Returns:
        The payoff function
    """

    def payoff(prices: NDArray[np.float64]) -> NDArray[np.float64]:
        on_strike = np.isclose(prices, K, rtol=1e-12, atol=0.0)
        result: NDArray[np.float64] = np.where(
            on_strike, 0.5, (prices > K).astype(np.float64)
        )
        return result

    return payoff


def _payoff_function(
    K: float, option_type: OptionType, payoff: Payoff | None
) -> Payoff:
    """The payoff to use: `payoff` if given, else a vanilla call or put on K."""
    if payoff is not None:
        return payoff
    sign = _sign(option_type)

    def vanilla(prices: NDArray[np.float64]) -> NDArray[np.float64]:
        result: NDArray[np.float64] = np.maximum(sign * (prices - K), 0.0)
        return result

    return vanilla


def _node_prices(S: float, up: float, step: int) -> NDArray[np.float64]:
    """Stock prices after `step` steps, from all up moves to all down moves.

    With d = 1/u the price after a net k up moves is S u^k. It is computed as
    S exp(k ln u) straight from S rather than stepped from node to node, so
    rounding does not build up, and a node with as many up as down moves is
    exactly S. That matters for a payoff that jumps at a strike equal to S,
    such as a digital: a node a rounding error above or below the strike
    would otherwise pay all or nothing at random.
    """
    net_ups = step - 2 * np.arange(step + 1)
    prices: NDArray[np.float64] = S * np.exp(math.log(up) * net_ups)
    return prices


@dataclass(frozen=True)
class BinomialLattice:
    """Every node of a Cox-Ross-Rubinstein tree, from today to expiry.

    Each list holds one array per time step, so element ``i`` is step ``i``.
    Within a step, node ``j`` has had ``j`` down moves, so node 0 has the
    highest price (the same order as `binomial_price`). `stock`, `value` and
    `exercise` run from step 0 to n_steps; `delta` and `bond` run from step 0
    to n_steps - 1, because there is no next step to hedge at expiry.

    Attributes:
        stock: Stock price at each node
        value: Option value at each node
        exercise: True where an American option is exercised early (the
            exercise value is strictly larger than the continuation value);
            all False for a European option and at expiry
        delta: Shares held in the portfolio that replicates the option over
            the next step, exp(-q dt) (V_up - V_down) / (S_up - S_down). The
            dividends are reinvested in the stock, so the holding grows to
            exp(q dt) * delta shares by the end of the step
        bond: Cash held in the same portfolio, continuation value minus
            delta * S (negative means borrowing). It earns the risk-free rate
        up: Up factor u
        down: Down factor d
        p: Risk-neutral probability of an up move
        dt: Length of one step in years
    """

    stock: list[NDArray[np.float64]]
    value: list[NDArray[np.float64]]
    exercise: list[NDArray[np.bool_]]
    delta: list[NDArray[np.float64]]
    bond: list[NDArray[np.float64]]
    up: float
    down: float
    p: float
    dt: float


def binomial_lattice(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    n_steps: int,
    option_type: OptionType = "call",
    american: bool = False,
    q: float = 0.0,
    payoff: Payoff | None = None,
) -> BinomialLattice:
    """Price an option on a Cox-Ross-Rubinstein tree and keep every node.

    The same backward induction as `binomial_price`, but returning the stock
    price, option value, early-exercise flag and replicating portfolio at
    each node, for display and teaching. For a vanilla payoff the value at
    the root equals `binomial_price`.

    Args:
        S: Current stock price, not negative
        K: Strike price, not negative (ignored when `payoff` is given)
        T: Time to expiry in years, positive
        r: Continuously compounded risk-free rate
        sigma: Annualised volatility, positive
        n_steps: Number of time steps, at least 1
        option_type: "call" or "put" (ignored when `payoff` is given)
        american: True to allow exercise at any node
        q: Continuous dividend yield
        payoff: Optional payoff function of the stock price, used at expiry
            and, for an American option, as the exercise value; for example
            `digital_call_payoff(K)`

    Returns:
        The lattice of node values

    Raises:
        ValueError: If an input is out of range; see crr_parameters
    """
    pay = _payoff_function(K, option_type, payoff)
    if S < 0 or K < 0:
        raise ValueError("S and K must not be negative")
    up, down, p = crr_parameters(T, r, sigma, n_steps, q)
    dt = T / n_steps
    discount = math.exp(-r * dt)
    dividend_discount = math.exp(-q * dt)

    stock = [_node_prices(S, up, step) for step in range(n_steps + 1)]
    value: list[NDArray[np.float64]] = [np.empty(0)] * (n_steps + 1)
    exercise: list[NDArray[np.bool_]] = [np.empty(0, dtype=bool)] * (n_steps + 1)
    delta: list[NDArray[np.float64]] = [np.empty(0)] * n_steps
    bond: list[NDArray[np.float64]] = [np.empty(0)] * n_steps

    value[n_steps] = np.asarray(pay(stock[n_steps]), dtype=np.float64)
    exercise[n_steps] = np.zeros(n_steps + 1, dtype=bool)

    for step in range(n_steps - 1, -1, -1):
        v_up, v_down = value[step + 1][:-1], value[step + 1][1:]
        continuation = discount * (p * v_up + (1 - p) * v_down)
        if american:
            intrinsic = np.asarray(pay(stock[step]), dtype=np.float64)
            exercise[step] = intrinsic > continuation
            value[step] = np.maximum(continuation, intrinsic)
        else:
            exercise[step] = np.zeros(step + 1, dtype=bool)
            value[step] = continuation
        # The portfolio that replicates the next step depends only on the two
        # successor values, whether or not the holder exercises here
        s_up, s_down = stock[step + 1][:-1], stock[step + 1][1:]
        delta[step] = dividend_discount * (v_up - v_down) / (s_up - s_down)
        bond[step] = continuation - delta[step] * stock[step]

    return BinomialLattice(stock, value, exercise, delta, bond, up, down, p, dt)


def terminal_distribution(
    S: float, T: float, r: float, sigma: float, n_steps: int, q: float = 0.0
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Stock prices at expiry on a CRR tree and their risk-neutral probabilities.

    The number of up moves is Binomial(n_steps, p), so the price after k up
    moves, S u^k d^(n - k), has probability C(n, k) p^k (1 - p)^(n - k).

    Args:
        S: Current stock price
        T: Time to expiry in years, positive
        r: Continuously compounded risk-free rate
        sigma: Annualised volatility, positive
        n_steps: Number of time steps, at least 1
        q: Continuous dividend yield

    Returns:
        Tuple of (prices, probabilities), indexed by the number of up moves
        k = 0, ..., n_steps

    Raises:
        ValueError: If an input is out of range; see crr_parameters
    """
    up, _, p = crr_parameters(T, r, sigma, n_steps, q)
    # The lattice's terminal prices run from all up to all down moves
    prices = _node_prices(S, up, n_steps)[::-1]
    probabilities: NDArray[np.float64] = binom.pmf(np.arange(n_steps + 1), n_steps, p)
    return prices, probabilities


def binomial_price_closed_form(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    n_steps: int,
    option_type: OptionType = "call",
    q: float = 0.0,
    payoff: Payoff | None = None,
) -> float:
    """Price a European option on a CRR tree as one sum, without induction.

    V_0 = exp(-r T) * sum_k C(n, k) p^k (1 - p)^(n - k) Payoff(S u^k d^(n - k))

    This equals `binomial_price` with american=False: backward induction
    computes the same discounted risk-neutral expectation one step at a time.

    Args:
        S: Current stock price, not negative
        K: Strike price, not negative (ignored when `payoff` is given)
        T: Time to expiry in years, positive
        r: Continuously compounded risk-free rate
        sigma: Annualised volatility, positive
        n_steps: Number of time steps, at least 1
        option_type: "call" or "put" (ignored when `payoff` is given)
        q: Continuous dividend yield
        payoff: Optional payoff function of the stock price at expiry

    Returns:
        Option price

    Raises:
        ValueError: If an input is out of range; see crr_parameters
    """
    pay = _payoff_function(K, option_type, payoff)
    if S < 0 or K < 0:
        raise ValueError("S and K must not be negative")
    prices, probabilities = terminal_distribution(S, T, r, sigma, n_steps, q)
    return float(math.exp(-r * T) * np.sum(probabilities * pay(prices)))
