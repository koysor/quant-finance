"""Unit tests for option payoff calculations."""

import numpy as np

from src.options.payoffs import (
    call_break_even,
    long_call_payoff,
    long_put_payoff,
    put_break_even,
    short_call_payoff,
    short_put_payoff,
)


class TestLongCallPayoff:
    """Tests for long call option payoff."""

    def test_in_the_money(self):
        """Long call ITM: stock > strike, profit = stock - strike - premium."""
        result = long_call_payoff(stock_price=110, strike=100, premium=5)
        assert result == 5.0  # 110 - 100 - 5

    def test_at_the_money(self):
        """Long call ATM: stock == strike, loss = premium."""
        result = long_call_payoff(stock_price=100, strike=100, premium=5)
        assert result == -5.0  # max(0, 0) - 5

    def test_out_of_the_money(self):
        """Long call OTM: stock < strike, loss = premium."""
        result = long_call_payoff(stock_price=90, strike=100, premium=5)
        assert result == -5.0  # max(0, -10) - 5

    def test_deep_in_the_money(self):
        """Long call deep ITM: large profit."""
        result = long_call_payoff(stock_price=200, strike=100, premium=10)
        assert result == 90.0  # 200 - 100 - 10

    def test_array_input(self):
        """Long call with array of stock prices."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        result = long_call_payoff(stock_price=stock_prices, strike=100, premium=5)
        expected = np.array([-5, -5, -5, 5, 15])
        np.testing.assert_array_equal(result, expected)


class TestShortCallPayoff:
    """Tests for short call option payoff."""

    def test_in_the_money(self):
        """Short call ITM: stock > strike, loss = stock - strike - premium."""
        result = short_call_payoff(stock_price=110, strike=100, premium=5)
        assert result == -5.0  # 5 - (110 - 100)

    def test_at_the_money(self):
        """Short call ATM: stock == strike, profit = premium."""
        result = short_call_payoff(stock_price=100, strike=100, premium=5)
        assert result == 5.0  # 5 - max(0, 0)

    def test_out_of_the_money(self):
        """Short call OTM: stock < strike, profit = premium."""
        result = short_call_payoff(stock_price=90, strike=100, premium=5)
        assert result == 5.0  # 5 - max(0, -10)

    def test_array_input(self):
        """Short call with array of stock prices."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        result = short_call_payoff(stock_price=stock_prices, strike=100, premium=5)
        expected = np.array([5, 5, 5, -5, -15])
        np.testing.assert_array_equal(result, expected)


class TestLongPutPayoff:
    """Tests for long put option payoff."""

    def test_in_the_money(self):
        """Long put ITM: stock < strike, profit = strike - stock - premium."""
        result = long_put_payoff(stock_price=90, strike=100, premium=5)
        assert result == 5.0  # 100 - 90 - 5

    def test_at_the_money(self):
        """Long put ATM: stock == strike, loss = premium."""
        result = long_put_payoff(stock_price=100, strike=100, premium=5)
        assert result == -5.0  # max(0, 0) - 5

    def test_out_of_the_money(self):
        """Long put OTM: stock > strike, loss = premium."""
        result = long_put_payoff(stock_price=110, strike=100, premium=5)
        assert result == -5.0  # max(0, -10) - 5

    def test_deep_in_the_money(self):
        """Long put deep ITM: stock goes to zero, max profit."""
        result = long_put_payoff(stock_price=0, strike=100, premium=10)
        assert result == 90.0  # 100 - 0 - 10

    def test_array_input(self):
        """Long put with array of stock prices."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        result = long_put_payoff(stock_price=stock_prices, strike=100, premium=5)
        expected = np.array([15, 5, -5, -5, -5])
        np.testing.assert_array_equal(result, expected)


class TestShortPutPayoff:
    """Tests for short put option payoff."""

    def test_in_the_money(self):
        """Short put ITM: stock < strike, loss = strike - stock - premium."""
        result = short_put_payoff(stock_price=90, strike=100, premium=5)
        assert result == -5.0  # 5 - (100 - 90)

    def test_at_the_money(self):
        """Short put ATM: stock == strike, profit = premium."""
        result = short_put_payoff(stock_price=100, strike=100, premium=5)
        assert result == 5.0  # 5 - max(0, 0)

    def test_out_of_the_money(self):
        """Short put OTM: stock > strike, profit = premium."""
        result = short_put_payoff(stock_price=110, strike=100, premium=5)
        assert result == 5.0  # 5 - max(0, -10)

    def test_array_input(self):
        """Short put with array of stock prices."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        result = short_put_payoff(stock_price=stock_prices, strike=100, premium=5)
        expected = np.array([-15, -5, 5, 5, 5])
        np.testing.assert_array_equal(result, expected)


class TestBreakEven:
    """Tests for break-even calculations."""

    def test_call_break_even(self):
        """Call break-even = strike + premium."""
        assert call_break_even(strike=100, premium=5) == 105

    def test_put_break_even(self):
        """Put break-even = strike - premium."""
        assert put_break_even(strike=100, premium=5) == 95

    def test_long_call_payoff_at_break_even(self):
        """Long call payoff at break-even should be zero."""
        be = call_break_even(strike=100, premium=5)
        result = long_call_payoff(stock_price=be, strike=100, premium=5)
        assert result == 0.0

    def test_long_put_payoff_at_break_even(self):
        """Long put payoff at break-even should be zero."""
        be = put_break_even(strike=100, premium=5)
        result = long_put_payoff(stock_price=be, strike=100, premium=5)
        assert result == 0.0


class TestPayoffSymmetry:
    """Tests verifying long/short payoff symmetry."""

    def test_call_symmetry(self):
        """Long call + short call = 0 (opposite positions)."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        long = long_call_payoff(stock_price=stock_prices, strike=100, premium=5)
        short = short_call_payoff(stock_price=stock_prices, strike=100, premium=5)
        np.testing.assert_array_equal(long + short, np.zeros(5))

    def test_put_symmetry(self):
        """Long put + short put = 0 (opposite positions)."""
        stock_prices = np.array([80, 90, 100, 110, 120])
        long = long_put_payoff(stock_price=stock_prices, strike=100, premium=5)
        short = short_put_payoff(stock_price=stock_prices, strike=100, premium=5)
        np.testing.assert_array_equal(long + short, np.zeros(5))
