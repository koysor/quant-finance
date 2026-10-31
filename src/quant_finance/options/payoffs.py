"""Option payoff calculations."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def long_call_payoff(
    stock_price: ArrayLike, strike: float, premium: float
) -> NDArray[np.float64]:
    """Calculate long call option payoff at expiration.

    Payoff = max(S_T - K, 0) - premium

    Args:
        stock_price: Stock price(s) at expiration
        strike: Strike price of the option
        premium: Premium paid for the option

    Returns:
        Payoff value(s)
    """
    return np.maximum(np.asarray(stock_price) - strike, 0) - premium


def short_call_payoff(
    stock_price: ArrayLike, strike: float, premium: float
) -> NDArray[np.float64]:
    """Calculate short call option payoff at expiration.

    Payoff = premium - max(S_T - K, 0)

    Args:
        stock_price: Stock price(s) at expiration
        strike: Strike price of the option
        premium: Premium received for the option

    Returns:
        Payoff value(s)
    """
    return premium - np.maximum(np.asarray(stock_price) - strike, 0)


def long_put_payoff(
    stock_price: ArrayLike, strike: float, premium: float
) -> NDArray[np.float64]:
    """Calculate long put option payoff at expiration.

    Payoff = max(K - S_T, 0) - premium

    Args:
        stock_price: Stock price(s) at expiration
        strike: Strike price of the option
        premium: Premium paid for the option

    Returns:
        Payoff value(s)
    """
    return np.maximum(strike - np.asarray(stock_price), 0) - premium


def short_put_payoff(
    stock_price: ArrayLike, strike: float, premium: float
) -> NDArray[np.float64]:
    """Calculate short put option payoff at expiration.

    Payoff = premium - max(K - S_T, 0)

    Args:
        stock_price: Stock price(s) at expiration
        strike: Strike price of the option
        premium: Premium received for the option

    Returns:
        Payoff value(s)
    """
    return premium - np.maximum(strike - np.asarray(stock_price), 0)


def call_break_even(strike: float, premium: float) -> float:
    """Calculate break-even price for a call option.

    Args:
        strike: Strike price
        premium: Option premium

    Returns:
        Break-even stock price
    """
    return strike + premium


def put_break_even(strike: float, premium: float) -> float:
    """Calculate break-even price for a put option.

    Args:
        strike: Strike price
        premium: Option premium

    Returns:
        Break-even stock price
    """
    return strike - premium
