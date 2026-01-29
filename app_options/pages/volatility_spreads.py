import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.markdown("### Volatility Spreads")

strategy = st.selectbox(
    "Volatility Spreads",
    [
        "Straddle",
        "Strangle",
        "Butterfly",
        "Condor",
        "Ratio Spread",
        "Christmas Tree",
        "Calendar Spread",
        "Time Butterfly",
        "Diagonal Spreads",
    ],
    index=0,
    help="Select a volatility spread strategy to visualise.",
)

st.markdown("---")

# Common parameters
col1, col2 = st.columns(2)

with col1:
    spot_price = st.number_input(
        "Current Stock Price",
        min_value=1.0,
        value=100.0,
        step=1.0,
        help="Current price of the underlying stock.",
    )

# Strategy-specific inputs and calculations
if strategy == "Straddle":
    with col1:
        strike = st.number_input(
            "Strike Price (ATM)",
            min_value=1.0,
            value=100.0,
            step=1.0,
            help="Strike price for both call and put (typically ATM).",
        )
    with col2:
        call_premium = st.number_input(
            "Call Premium", min_value=0.0, value=5.0, step=0.5
        )
        put_premium = st.number_input("Put Premium", min_value=0.0, value=5.0, step=0.5)

    total_premium = call_premium + put_premium
    stock_prices = np.linspace(strike * 0.5, strike * 1.5, 200)

    # Long straddle payoff
    call_payoff = np.maximum(stock_prices - strike, 0)
    put_payoff = np.maximum(strike - stock_prices, 0)
    payoff = call_payoff + put_payoff - total_premium

    break_even_lower = strike - total_premium
    break_even_upper = strike + total_premium

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Straddle P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=strike,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Strike: {strike:.0f}",
    )
    ax.axvline(
        x=break_even_lower,
        color="green",
        linestyle="--",
        linewidth=1,
        label=f"BE Lower: {break_even_lower:.2f}",
    )
    ax.axvline(
        x=break_even_upper,
        color="green",
        linestyle=":",
        linewidth=1,
        label=f"BE Upper: {break_even_upper:.2f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Long Straddle Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
A **Straddle** involves buying both a call and a put option at the same strike price and expiration date.

**When to use:** Traders use straddles when they expect significant price movement but are uncertain
about the direction. Common before earnings announcements or major economic events.

**How traders profit:**
- The stock must move significantly in either direction beyond the break-even points
- Profit is unlimited if the stock rises substantially
- Profit is substantial (but capped at strike - premium) if the stock falls to zero

**Risk:** Maximum loss equals the total premium paid, occurring when the stock closes exactly at the strike price.
        """)

        st.latex(
            r"\text{Payoff} = \max(S_T - K, 0) + \max(K - S_T, 0) - \text{Premium}"
        )
        st.markdown(f"**Max Loss:** £{total_premium:.2f} (total premium paid)")
        st.markdown(
            f"**Break-even Points:** £{break_even_lower:.2f} and £{break_even_upper:.2f}"
        )

elif strategy == "Strangle":
    with col1:
        put_strike = st.number_input(
            "Put Strike (Lower)",
            min_value=1.0,
            value=95.0,
            step=1.0,
            help="Strike price for the put option (OTM).",
        )
        call_strike = st.number_input(
            "Call Strike (Higher)",
            min_value=1.0,
            value=105.0,
            step=1.0,
            help="Strike price for the call option (OTM).",
        )
    with col2:
        call_premium = st.number_input(
            "Call Premium", min_value=0.0, value=3.0, step=0.5
        )
        put_premium = st.number_input("Put Premium", min_value=0.0, value=3.0, step=0.5)

    total_premium = call_premium + put_premium
    stock_prices = np.linspace(put_strike * 0.5, call_strike * 1.5, 200)

    call_payoff = np.maximum(stock_prices - call_strike, 0)
    put_payoff = np.maximum(put_strike - stock_prices, 0)
    payoff = call_payoff + put_payoff - total_premium

    break_even_lower = put_strike - total_premium
    break_even_upper = call_strike + total_premium

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Strangle P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=put_strike,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Put Strike: {put_strike:.0f}",
    )
    ax.axvline(
        x=call_strike,
        color="red",
        linestyle=":",
        linewidth=1,
        label=f"Call Strike: {call_strike:.0f}",
    )
    ax.axvline(
        x=break_even_lower,
        color="green",
        linestyle="--",
        linewidth=1,
        label=f"BE Lower: {break_even_lower:.2f}",
    )
    ax.axvline(
        x=break_even_upper,
        color="green",
        linestyle=":",
        linewidth=1,
        label=f"BE Upper: {break_even_upper:.2f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Long Strangle Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
A**Strangle** involves buying an OTM call and an OTM put with the **same expiration** but **different strike prices**.

**When to use:** Similar to a straddle but cheaper, used when expecting large price movement in either
direction. The stock needs to move further to profit compared to a straddle.

**How traders profit:**
- Lower cost than a straddle means smaller potential loss
- Requires larger price movement to reach profitability
- Unlimited profit potential on the upside, substantial on the downside

**Risk:** Maximum loss is the total premium paid, occurring if the stock stays between the two strikes.
        """)

        st.latex(
            r"\text{Payoff} = \max(S_T - K_{call}, 0) + \max(K_{put} - S_T, 0) - \text{Premium}"
        )
        st.markdown(f"**Max Loss:** £{total_premium:.2f} (total premium paid)")
        st.markdown(
            f"**Break-even Points:** £{break_even_lower:.2f} and £{break_even_upper:.2f}"
        )

    st.info(
        "A straddle uses a call and a put with the same strike; a strangle uses a call and a put with different strikes, both on the same expiry. Straddles cost more but need less movement to profit, while strangles are cheaper but require a bigger move.  "
        "\n- Straddles are more expensive because both options are at-the-money, so they have higher premiums. "
        "\n- Strangles are cheaper because both options are out-of-the-money and have lower premiums. "
    )

elif strategy == "Butterfly":
    with col1:
        lower_strike = st.number_input(
            "Lower Strike (K1)",
            min_value=1.0,
            value=90.0,
            step=1.0,
        )
        middle_strike = st.number_input(
            "Middle Strike (K2)",
            min_value=1.0,
            value=100.0,
            step=1.0,
        )
        upper_strike = st.number_input(
            "Upper Strike (K3)",
            min_value=1.0,
            value=110.0,
            step=1.0,
        )
    with col2:
        lower_premium = st.number_input(
            "Lower Call Premium (Buy)", min_value=0.0, value=12.0, step=0.5
        )
        middle_premium = st.number_input(
            "Middle Call Premium (Sell x2)", min_value=0.0, value=6.0, step=0.5
        )
        upper_premium = st.number_input(
            "Upper Call Premium (Buy)", min_value=0.0, value=2.0, step=0.5
        )

    net_debit = lower_premium - 2 * middle_premium + upper_premium
    stock_prices = np.linspace(lower_strike * 0.7, upper_strike * 1.3, 200)

    # Long butterfly: +1 K1 call, -2 K2 calls, +1 K3 call
    long_k1 = np.maximum(stock_prices - lower_strike, 0)
    short_k2 = -2 * np.maximum(stock_prices - middle_strike, 0)
    long_k3 = np.maximum(stock_prices - upper_strike, 0)
    payoff = long_k1 + short_k2 + long_k3 - net_debit

    max_profit = middle_strike - lower_strike - net_debit
    break_even_lower = lower_strike + net_debit
    break_even_upper = upper_strike - net_debit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Butterfly P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=lower_strike,
        color="red",
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label=f"K1: {lower_strike:.0f}",
    )
    ax.axvline(
        x=middle_strike,
        color="red",
        linestyle="-",
        linewidth=1,
        label=f"K2: {middle_strike:.0f}",
    )
    ax.axvline(
        x=upper_strike,
        color="red",
        linestyle=":",
        linewidth=1,
        alpha=0.7,
        label=f"K3: {upper_strike:.0f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Long Butterfly Spread Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Butterfly Spread** combines a bull spread and a bear spread with three strike prices.
Buy 1 call at K1, sell 2 calls at K2, buy 1 call at K3 (where K1 < K2 < K3).

**When to use:** When you expect the stock to stay near the middle strike price (low volatility expectation).
Ideal when implied volatility is high and expected to decrease.

**How traders profit:**
- Maximum profit occurs when the stock closes exactly at the middle strike
- Profits from time decay if the stock stays range-bound
- Limited risk strategy with defined maximum loss

**Risk:** Maximum loss is the net premium paid (net debit), occurring if stock moves significantly in either direction.
        """)

        st.markdown(f"**Net Debit:** £{net_debit:.2f}")
        st.markdown(f"**Max Profit:** £{max_profit:.2f} (at middle strike)")
        st.markdown(f"**Max Loss:** £{net_debit:.2f}")
        st.markdown(
            f"**Break-even Points:** £{break_even_lower:.2f} and £{break_even_upper:.2f}"
        )

elif strategy == "Condor":
    with col1:
        k1 = st.number_input("Strike K1 (Lowest)", min_value=1.0, value=85.0, step=1.0)
        k2 = st.number_input("Strike K2", min_value=1.0, value=95.0, step=1.0)
        k3 = st.number_input("Strike K3", min_value=1.0, value=105.0, step=1.0)
        k4 = st.number_input(
            "Strike K4 (Highest)", min_value=1.0, value=115.0, step=1.0
        )
    with col2:
        p1 = st.number_input(
            "K1 Call Premium (Buy)", min_value=0.0, value=16.0, step=0.5
        )
        p2 = st.number_input(
            "K2 Call Premium (Sell)", min_value=0.0, value=8.0, step=0.5
        )
        p3 = st.number_input(
            "K3 Call Premium (Sell)", min_value=0.0, value=4.0, step=0.5
        )
        p4 = st.number_input(
            "K4 Call Premium (Buy)", min_value=0.0, value=1.0, step=0.5
        )

    net_debit = p1 - p2 - p3 + p4
    stock_prices = np.linspace(k1 * 0.7, k4 * 1.3, 200)

    # Long condor: +1 K1 call, -1 K2 call, -1 K3 call, +1 K4 call
    payoff = (
        np.maximum(stock_prices - k1, 0)
        - np.maximum(stock_prices - k2, 0)
        - np.maximum(stock_prices - k3, 0)
        + np.maximum(stock_prices - k4, 0)
        - net_debit
    )

    max_profit = k2 - k1 - net_debit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Condor P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    for k, label in [(k1, "K1"), (k2, "K2"), (k3, "K3"), (k4, "K4")]:
        ax.axvline(
            x=k,
            color="red",
            linestyle="--",
            linewidth=1,
            alpha=0.6,
            label=f"{label}: {k:.0f}",
        )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Long Condor Spread Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Condor Spread** uses four strike prices: Buy K1 call, sell K2 call, sell K3 call, buy K4 call.
Similar to a butterfly but with a wider profit zone.

**When to use:** When expecting low volatility and the stock to remain within a range.
Offers a wider profit zone than a butterfly but lower maximum profit.

**How traders profit:**
- Maximum profit when stock stays between K2 and K3
- Wider "sweet spot" compared to butterfly
- Benefits from time decay when stock is in the profit zone

**Risk:** Maximum loss is limited to the net debit paid.
        """)

        st.markdown(f"**Net Debit:** £{net_debit:.2f}")
        st.markdown(f"**Max Profit:** £{max_profit:.2f} (between K2 and K3)")
        st.markdown(f"**Max Loss:** £{net_debit:.2f}")

elif strategy == "Ratio Spread":
    with col1:
        lower_strike = st.number_input(
            "Lower Strike (Buy)",
            min_value=1.0,
            value=100.0,
            step=1.0,
        )
        upper_strike = st.number_input(
            "Upper Strike (Sell)",
            min_value=1.0,
            value=110.0,
            step=1.0,
        )
        ratio = st.selectbox("Ratio (Buy:Sell)", ["1:2", "1:3", "2:3"], index=0)
    with col2:
        lower_premium = st.number_input(
            "Lower Call Premium", min_value=0.0, value=8.0, step=0.5
        )
        upper_premium = st.number_input(
            "Upper Call Premium", min_value=0.0, value=3.0, step=0.5
        )

    if ratio == "1:2":
        buy_qty, sell_qty = 1, 2
    elif ratio == "1:3":
        buy_qty, sell_qty = 1, 3
    else:
        buy_qty, sell_qty = 2, 3

    net_credit = sell_qty * upper_premium - buy_qty * lower_premium
    stock_prices = np.linspace(lower_strike * 0.7, upper_strike * 1.5, 200)

    # Ratio call spread
    long_calls = buy_qty * np.maximum(stock_prices - lower_strike, 0)
    short_calls = sell_qty * np.maximum(stock_prices - upper_strike, 0)
    payoff = long_calls - short_calls + net_credit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Ratio Spread P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=lower_strike,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Buy Strike: {lower_strike:.0f}",
    )
    ax.axvline(
        x=upper_strike,
        color="orange",
        linestyle="--",
        linewidth=1,
        label=f"Sell Strike: {upper_strike:.0f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title(
        f"Ratio Call Spread ({buy_qty}:{sell_qty}) Payoff",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown(f"""
**Ratio Spread** involves buying calls at one strike and selling more calls at a higher strike.
In this {buy_qty}:{sell_qty} ratio, you buy {buy_qty} call(s) at the lower strike and sell {sell_qty} call(s) at the upper strike.

**When to use:** When you're moderately bullish but want to reduce cost or create a credit.
Best when you expect the stock to rise to the short strike but not exceed it significantly.

**How traders profit:**
- Maximum profit at the upper strike price
- Can be established for a credit if premium received exceeds premium paid
- Profits from moderate upward movement

**Risk:** Unlimited risk above the upper strike due to the extra short calls.
This strategy requires careful risk management.
        """)

        st.markdown(
            f"**Net Credit/Debit:** £{net_credit:.2f} ({'Credit' if net_credit > 0 else 'Debit'})"
        )
        st.markdown(f"**Max Profit:** At upper strike £{upper_strike:.0f}")
        st.markdown("**Risk:** Unlimited above upper strike")

elif strategy == "Christmas Tree":
    with col1:
        k1 = st.number_input("Strike K1 (Buy 1)", min_value=1.0, value=95.0, step=1.0)
        k2 = st.number_input("Strike K2 (Sell 1)", min_value=1.0, value=100.0, step=1.0)
        k3 = st.number_input("Strike K3 (Sell 1)", min_value=1.0, value=105.0, step=1.0)
    with col2:
        p1 = st.number_input("K1 Premium (Buy)", min_value=0.0, value=8.0, step=0.5)
        p2 = st.number_input("K2 Premium (Sell)", min_value=0.0, value=5.0, step=0.5)
        p3 = st.number_input("K3 Premium (Sell)", min_value=0.0, value=3.0, step=0.5)

    net_debit = p1 - p2 - p3
    stock_prices = np.linspace(k1 * 0.7, k3 * 1.4, 200)

    # Christmas tree: +1 K1 call, -1 K2 call, -1 K3 call
    payoff = (
        np.maximum(stock_prices - k1, 0)
        - np.maximum(stock_prices - k2, 0)
        - np.maximum(stock_prices - k3, 0)
        - net_debit
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Christmas Tree P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=k1, color="green", linestyle="--", linewidth=1, label=f"K1 (Buy): {k1:.0f}"
    )
    ax.axvline(
        x=k2, color="red", linestyle="--", linewidth=1, label=f"K2 (Sell): {k2:.0f}"
    )
    ax.axvline(
        x=k3, color="red", linestyle=":", linewidth=1, label=f"K3 (Sell): {k3:.0f}"
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Christmas Tree Spread Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Christmas Tree** (also called a Ladder) involves buying one call at a lower strike and
selling calls at two different higher strikes. The payoff diagram resembles a Christmas tree shape.

**When to use:** When moderately bullish with a specific price target in mind.
Useful when you want to profit from a move up to a certain level but want protection against further upside.

**How traders profit:**
- Maximum profit achieved at the middle strike (K2)
- Lower cost than a simple bull spread
- Can sometimes be established for a credit

**Risk:** Unlimited risk if the stock rises significantly above K3.
Loss also possible if stock stays below K1.
        """)

        max_profit = k2 - k1 - net_debit
        st.markdown(
            f"**Net Debit/Credit:** £{net_debit:.2f} ({'Debit' if net_debit > 0 else 'Credit'})"
        )
        st.markdown(f"**Max Profit:** £{max_profit:.2f} (at K2)")
        st.markdown("**Risk:** Unlimited above K3")

elif strategy == "Calendar Spread":
    with col1:
        strike = st.number_input(
            "Strike Price",
            min_value=1.0,
            value=100.0,
            step=1.0,
            help="Same strike for both options",
        )
    with col2:
        near_premium = st.number_input(
            "Near-term Premium (Sell)", min_value=0.0, value=3.0, step=0.5
        )
        far_premium = st.number_input(
            "Far-term Premium (Buy)", min_value=0.0, value=6.0, step=0.5
        )
        iv_far = st.slider("Far-term IV (%)", 10, 100, 35) / 100

    net_debit = far_premium - near_premium
    stock_prices = np.linspace(strike * 0.7, strike * 1.3, 200)

    # Near-term option is at expiry (intrinsic value only)
    near_payoff = -np.maximum(stock_prices - strike, 0)  # Short call at expiry

    # Far-term option still has time value (simplified Black-Scholes-like approximation)
    remaining_time = 30 / 365  # Assume 30 days left on far option
    d1 = (np.log(stock_prices / strike) + (0.05 + iv_far**2 / 2) * remaining_time) / (
        iv_far * np.sqrt(remaining_time)
    )
    from scipy.stats import norm

    far_value = stock_prices * norm.cdf(d1) - strike * np.exp(
        -0.05 * remaining_time
    ) * norm.cdf(d1 - iv_far * np.sqrt(remaining_time))

    payoff = near_payoff + far_value - net_debit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Calendar Spread P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=strike,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Strike: {strike:.0f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Near-term Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title(
        "Calendar Spread Payoff (at near-term expiry)", fontsize=14, fontweight="bold"
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Calendar Spread** (Time Spread) involves selling a near-term option and buying a longer-term
option at the same strike price. Also known as a horizontal spread.

**When to use:** When expecting the stock to stay near the strike price and volatility to increase.
Profits from the faster time decay of the near-term option.

**How traders profit:**
- Near-term option decays faster than far-term option
- Maximum profit when stock is at the strike at near-term expiration
- Can also profit from increasing implied volatility

**Risk:** Loss if stock moves significantly away from strike or if implied volatility decreases.
        """)

        st.markdown(f"**Net Debit:** £{net_debit:.2f}")
        st.markdown(
            f"**Max Profit:** At strike price £{strike:.0f} at near-term expiration"
        )
        st.markdown("**Max Loss:** Limited to net debit paid")

elif strategy == "Time Butterfly":
    with col1:
        strike = st.number_input(
            "Strike Price",
            min_value=1.0,
            value=100.0,
            step=1.0,
        )
    with col2:
        near_premium = st.number_input(
            "Near-term Premium (Buy)", min_value=0.0, value=2.0, step=0.5
        )
        mid_premium = st.number_input(
            "Mid-term Premium (Sell x2)", min_value=0.0, value=4.0, step=0.5
        )
        far_premium = st.number_input(
            "Far-term Premium (Buy)", min_value=0.0, value=6.0, step=0.5
        )
        iv = st.slider("Implied Volatility (%)", 10, 100, 30) / 100

    net_debit = near_premium - 2 * mid_premium + far_premium
    stock_prices = np.linspace(strike * 0.7, strike * 1.3, 200)

    # Time butterfly approximation at mid-term expiry
    from scipy.stats import norm

    remaining_time_far = 30 / 365
    d1_far = (
        np.log(stock_prices / strike) + (0.05 + iv**2 / 2) * remaining_time_far
    ) / (iv * np.sqrt(remaining_time_far))
    far_value = stock_prices * norm.cdf(d1_far) - strike * np.exp(
        -0.05 * remaining_time_far
    ) * norm.cdf(d1_far - iv * np.sqrt(remaining_time_far))

    # Near and mid are at expiry (intrinsic only)
    near_payoff = np.maximum(stock_prices - strike, 0)
    mid_payoff = -2 * np.maximum(stock_prices - strike, 0)

    payoff = near_payoff + mid_payoff + far_value - net_debit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Time Butterfly P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=strike,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Strike: {strike:.0f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Mid-term Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Time Butterfly Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Time Butterfly** combines calendar spreads using three expiration dates at the same strike.
Buy near-term, sell 2x mid-term, buy far-term options.

**When to use:** When expecting the stock to stay at the strike price through multiple time periods.
A more complex time decay play than a simple calendar spread.

**How traders profit:**
- Profits from differential time decay across three expirations
- Maximum profit typically at mid-term expiration when stock is at strike
- Can profit from specific volatility term structure scenarios

**Risk:** Limited to net premium paid. More complex to manage than single calendar spreads.
        """)

        st.markdown(f"**Net Debit:** £{net_debit:.2f}")
        st.markdown("**Best case:** Stock at strike at mid-term expiration")

elif strategy == "Diagonal Spreads":
    with col1:
        near_strike = st.number_input(
            "Near-term Strike (Sell)",
            min_value=1.0,
            value=105.0,
            step=1.0,
        )
        far_strike = st.number_input(
            "Far-term Strike (Buy)",
            min_value=1.0,
            value=100.0,
            step=1.0,
        )
    with col2:
        near_premium = st.number_input(
            "Near-term Premium (Sell)", min_value=0.0, value=3.0, step=0.5
        )
        far_premium = st.number_input(
            "Far-term Premium (Buy)", min_value=0.0, value=7.0, step=0.5
        )
        iv = st.slider("Implied Volatility (%)", 10, 100, 30) / 100

    net_debit = far_premium - near_premium
    stock_prices = np.linspace(far_strike * 0.7, near_strike * 1.4, 200)

    from scipy.stats import norm

    # At near-term expiry
    near_payoff = -np.maximum(stock_prices - near_strike, 0)

    # Far-term option still has time value
    remaining_time = 30 / 365
    d1 = (np.log(stock_prices / far_strike) + (0.05 + iv**2 / 2) * remaining_time) / (
        iv * np.sqrt(remaining_time)
    )
    far_value = stock_prices * norm.cdf(d1) - far_strike * np.exp(
        -0.05 * remaining_time
    ) * norm.cdf(d1 - iv * np.sqrt(remaining_time))

    payoff = near_payoff + far_value - net_debit

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Diagonal Spread P/L")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axvline(
        x=near_strike,
        color="orange",
        linestyle="--",
        linewidth=1,
        label=f"Near Strike: {near_strike:.0f}",
    )
    ax.axvline(
        x=far_strike,
        color="blue",
        linestyle="--",
        linewidth=1,
        label=f"Far Strike: {far_strike:.0f}",
    )
    ax.fill_between(
        stock_prices, payoff, 0, where=(payoff > 0), alpha=0.3, color="green"
    )
    ax.fill_between(stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red")
    ax.set_xlabel("Stock Price at Near-term Expiration")
    ax.set_ylabel("Profit/Loss")
    ax.set_title("Diagonal Spread Payoff", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    chart_col, text_col = st.columns([3, 2])

    with chart_col:
        st.pyplot(fig)

    with text_col:
        st.markdown("#### Strategy Explanation")
        st.markdown("""
**Diagonal Spread** combines elements of vertical and calendar spreads by using different
strikes AND different expirations. Sell near-term option at one strike, buy far-term at another.

**When to use:** When you have a directional bias combined with a time decay view.
- Bullish diagonal: Buy lower strike far-term, sell higher strike near-term
- Bearish diagonal: Buy higher strike far-term, sell lower strike near-term

**How traders profit:**
- Combines directional movement with time decay
- Near-term option decays faster, potentially expiring worthless
- Far-term option can be sold or exercised for profit

**Risk:** More complex risk profile than simple spreads.
Loss if stock moves significantly against the position or IV collapses.
        """)

        st.markdown(f"**Net Debit:** £{net_debit:.2f}")
        st.markdown(
            f"**Ideal scenario:** Stock at near-term strike ({near_strike:.0f}) at near-term expiry"
        )
        st.markdown("**Max Loss:** Limited to net debit if stock falls significantly")
