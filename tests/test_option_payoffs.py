"""Unit tests for option payoff calculations."""

import numpy as np

from quant_finance.options.payoffs import (
    OptionLeg,
    call_break_even,
    long_call_payoff,
    long_put_payoff,
    put_break_even,
    short_call_payoff,
    short_put_payoff,
    strategy_payoff,
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


class TestStrategyPayoff:
    """Tests for multi-leg strategy payoffs."""

    PRICES = np.linspace(50.0, 150.0, 201)

    def test_single_legs_match_the_individual_payoffs(self):
        long_call = strategy_payoff(self.PRICES, [OptionLeg("call", 100)], 5.0)
        short_put = strategy_payoff(self.PRICES, [OptionLeg("put", 100, -1)], -5.0)
        np.testing.assert_array_equal(
            long_call, long_call_payoff(self.PRICES, 100, 5.0)
        )
        np.testing.assert_array_equal(
            short_put, short_put_payoff(self.PRICES, 100, 5.0)
        )

    def test_straddle_equals_the_sum_of_its_legs(self):
        legs = [OptionLeg("call", 100), OptionLeg("put", 100)]
        np.testing.assert_allclose(
            strategy_payoff(self.PRICES, legs, 10.0),
            long_call_payoff(self.PRICES, 100, 5.0)
            + long_put_payoff(self.PRICES, 100, 5.0),
        )

    def test_straddle_break_evens_give_zero_profit(self):
        legs = [OptionLeg("call", 100), OptionLeg("put", 100)]
        np.testing.assert_allclose(strategy_payoff([90.0, 110.0], legs, 10.0), 0.0)

    def test_butterfly_peaks_at_the_middle_strike(self):
        legs = [
            OptionLeg("call", 90),
            OptionLeg("call", 100, -2),
            OptionLeg("call", 110),
        ]
        payoff = strategy_payoff(self.PRICES, legs, 2.0)
        assert self.PRICES[np.argmax(payoff)] == 100.0
        assert payoff.max() == 8.0
        assert payoff.min() == -2.0

    def test_condor_is_flat_between_the_short_strikes(self):
        legs = [
            OptionLeg("call", 80),
            OptionLeg("call", 90, -1),
            OptionLeg("call", 110, -1),
            OptionLeg("call", 120),
        ]
        np.testing.assert_allclose(strategy_payoff([90.0, 100.0, 110.0], legs), 10.0)

    def test_net_credit_adds_to_the_payoff(self):
        legs = [OptionLeg("call", 100, 1), OptionLeg("call", 110, -2)]
        assert strategy_payoff(100.0, legs, net_premium=-3.0) == 3.0

    def test_accepts_a_scalar_price(self):
        assert np.ndim(strategy_payoff(100.0, [OptionLeg("call", 90)])) == 0

    def test_does_not_modify_the_input_prices(self):
        prices = self.PRICES.copy()
        strategy_payoff(prices, [OptionLeg("call", 100)], 1.0)
        np.testing.assert_array_equal(prices, self.PRICES)
