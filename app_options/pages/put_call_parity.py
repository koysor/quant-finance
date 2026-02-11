import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(layout="wide")
st.markdown("### Put-Call Parity")

st.write(
    "Put-Call Parity is a fundamental principle in options pricing that establishes "
    "a precise relationship between European call and put option prices. This no-arbitrage "
    "condition ensures that two portfolios with identical payoffs at expiration must have "
    "the same value today, preventing risk-free profit opportunities."
)

st.info(
    "A portfolio of a long call option plus a zero-coupon bond paying the strike price at "
    "maturity has exactly the same payoff as a portfolio of a long put option plus the "
    "underlying stock. Because they have identical payoffs in every possible future state, "
    "the no-arbitrage principle dictates they must cost the same today."
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def black_scholes_call(S, K, T, r, sigma):
    """European call price via Black-Scholes."""
    if T <= 0:
        return np.maximum(S - K, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def black_scholes_put(S, K, T, r, sigma):
    """European put price via Black-Scholes."""
    if T <= 0:
        return np.maximum(K - S, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


# ---------------------------------------------------------------------------
# Section 1 – The Formula
# ---------------------------------------------------------------------------

st.markdown("#### The Put-Call Parity Relationship")

st.write("The parity condition can be expressed in two equivalent forms:")

with st.expander(label="Put-Call Parity Formula", expanded=True):
    latex_parity = r"""
        C + K e^{-rT} = P + S_0 \\ \\

        \text{or equivalently:} \\
        C - P = S_0 - K e^{-rT} \\ \\

        where: \\
        C = \text{European call option price} \\
        P = \text{European put option price} \\
        S_0 = \text{current stock price} \\
        K = \text{strike price} \\
        r = \text{risk-free interest rate (continuous compounding)} \\
        T = \text{time to expiration (years)} \\
        K e^{-rT} = \text{present value of the strike price}
        """
    st.code(latex_parity, language="latex")
    st.latex(latex_parity)

st.write(
    "The left-hand side is known as a **Fiduciary Call** — a long call plus a zero-coupon "
    "bond that pays $K$ at maturity. The right-hand side is a **Protective Put** — a long "
    "put plus one share of the underlying stock."
)

st.write(
    "The risk-free rate $r$ enters through the discounting term $K e^{-rT}$, which is the "
    "present value of the strike price. An increase in $r$ lowers $K e^{-rT}$, reducing the "
    "cost of the fiduciary call and narrowing the gap $C - P$. Conversely a decrease in $r$ "
    "raises the present value of the bond, widening $C - P$."
)


# ---------------------------------------------------------------------------
# Section 2 – Component Breakdown at Expiration
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Portfolio Components at Expiration")

st.write(
    "The plot below shows how the four individual components combine into two portfolios "
    "with identical payoffs at expiration, regardless of the final stock price $S_T$."
)

col_param1, col_param2 = st.columns(2)

with col_param1:
    strike_exp = st.slider(
        "Strike Price (K)",
        min_value=50.0,
        max_value=150.0,
        value=100.0,
        step=5.0,
        key="strike_exp",
    )

with col_param2:
    show_components_exp = st.checkbox(
        "Show individual components",
        value=True,
        key="show_comp_exp",
    )

s_T = np.linspace(max(0, strike_exp - 50), strike_exp + 50, 200)

call_payoff = np.maximum(s_T - strike_exp, 0)
put_payoff = np.maximum(strike_exp - s_T, 0)
bond_value = np.full_like(s_T, strike_exp)
stock_value = s_T

portfolio_A = call_payoff + bond_value
portfolio_B = put_payoff + stock_value

chart_col, text_col = st.columns([3, 2])

with chart_col:
    fig, ax = plt.subplots(figsize=(10, 6))

    if show_components_exp:
        ax.plot(s_T, call_payoff, "b--", alpha=0.6, linewidth=1, label="Call Payoff")
        ax.plot(s_T, put_payoff, "r--", alpha=0.6, linewidth=1, label="Put Payoff")
        ax.plot(
            s_T, stock_value, "g--", alpha=0.6, linewidth=1, label="Stock Value (S_T)"
        )
        ax.plot(
            s_T,
            bond_value,
            color="orange",
            linestyle="--",
            alpha=0.6,
            linewidth=1,
            label=f"Bond Value (K={strike_exp:.0f})",
        )

        ax.fill_between(
            s_T, call_payoff, 0, where=(call_payoff > 0), alpha=0.15, color="blue"
        )
        ax.fill_between(
            s_T, put_payoff, 0, where=(put_payoff > 0), alpha=0.15, color="red"
        )

    ax.plot(
        s_T,
        portfolio_A,
        color="purple",
        linewidth=2.5,
        label="Portfolio A (Call + Bond)",
    )
    ax.plot(
        s_T,
        portfolio_B,
        color="teal",
        linewidth=2.5,
        linestyle="--",
        label="Portfolio B (Put + Stock)",
    )

    ax.axvline(
        x=strike_exp,
        color="grey",
        linestyle=":",
        alpha=0.5,
        label=f"Strike: £{strike_exp:.0f}",
    )

    ax.set_xlabel("Stock Price at Expiration (S_T)", fontsize=12)
    ax.set_ylabel("Value at Expiration", fontsize=12)
    ax.set_title(
        "Put-Call Parity: Component Breakdown at Expiration",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)

with text_col:
    st.markdown("#### Portfolio Breakdown")
    st.markdown(f"""
**Portfolio A (Fiduciary Call):**
- Long call option: max(S_T - K, 0)
- Zero-coupon bond paying K: £{strike_exp:.0f}
- **Total value: max(S_T, K)**

**Portfolio B (Protective Put):**
- Long put option: max(K - S_T, 0)
- Underlying stock: S_T
- **Total value: max(S_T, K)**

Both portfolios always equal max(S_T, K) at expiration:
- If S_T > K, Portfolio A = (S_T - K) + K = S_T
- If S_T < K, Portfolio A = 0 + K = K
- If S_T > K, Portfolio B = 0 + S_T = S_T
- If S_T < K, Portfolio B = (K - S_T) + S_T = K

The purple and teal lines overlap perfectly, confirming the parity relationship.
""")


# ---------------------------------------------------------------------------
# Section 3 – Arbitrage Detection Calculator
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Arbitrage Detection Calculator")

st.write(
    "Enter market prices for the call, put, and stock to check whether put-call parity "
    "holds. If it is violated, the calculator identifies the arbitrage trade and profit."
)

col_arb1, col_arb2, col_arb3 = st.columns(3)

with col_arb1:
    st.markdown("**Market Prices**")
    S0_arb = st.number_input(
        "Current Stock Price (S₀)",
        min_value=1.0,
        value=100.0,
        step=1.0,
        key="s0_arb",
    )
    K_arb = st.number_input(
        "Strike Price (K)", min_value=1.0, value=100.0, step=1.0, key="k_arb"
    )

with col_arb2:
    st.markdown("**Option Prices**")
    C_market = st.number_input(
        "Call Price (C)", min_value=0.0, value=10.0, step=0.5, key="c_market"
    )
    P_market = st.number_input(
        "Put Price (P)", min_value=0.0, value=9.5, step=0.5, key="p_market"
    )

with col_arb3:
    st.markdown("**Parameters**")
    r_arb = (
        st.slider(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            key="r_arb",
        )
        / 100
    )
    T_arb = st.slider(
        "Time to Expiration (years)",
        min_value=0.1,
        max_value=2.0,
        value=1.0,
        step=0.1,
        key="t_arb",
    )

PV_K = K_arb * np.exp(-r_arb * T_arb)
left_side = C_market + PV_K  # Portfolio A value
right_side = P_market + S0_arb  # Portfolio B value
difference = left_side - right_side

C_implied = P_market + S0_arb - PV_K
P_implied = C_market + PV_K - S0_arb

tolerance = 0.10

st.markdown("##### Parity Check Results")

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.metric(label="Portfolio A (Call + Bond)", value=f"£{left_side:.2f}")
    st.metric(label="Portfolio B (Put + Stock)", value=f"£{right_side:.2f}")

with col_res2:
    st.metric(label="Difference (A − B)", value=f"£{difference:.2f}")
    st.metric(label="Present Value of Strike", value=f"£{PV_K:.2f}")

if abs(difference) < tolerance:
    st.success(
        "Put-Call Parity holds (within tolerance). No arbitrage opportunity exists."
    )
else:
    st.error("Put-Call Parity is violated! Arbitrage opportunity detected.")

    st.markdown("##### Arbitrage Strategy")

    if difference > 0:
        st.markdown(f"""
**Portfolio A is overpriced relative to Portfolio B.**

Sell the expensive portfolio, buy the cheap one:

1. **Sell** the call option — receive £{C_market:.2f}
2. **Borrow** the present value of K (sell the bond) — receive £{PV_K:.2f}
3. **Buy** the put option — pay £{P_market:.2f}
4. **Buy** the stock — pay £{S0_arb:.2f}

**Net cash flow today: £{difference:.2f}** (risk-free profit)

At expiration the long put + long stock position exactly offsets the short call +
bond repayment obligation in every scenario.
""")
    else:
        st.markdown(f"""
**Portfolio B is overpriced relative to Portfolio A.**

Sell the expensive portfolio, buy the cheap one:

1. **Buy** the call option — pay £{C_market:.2f}
2. **Lend** PV(K) (buy the bond) — pay £{PV_K:.2f}
3. **Sell** the put option — receive £{P_market:.2f}
4. **Short** the stock — receive £{S0_arb:.2f}

**Net cash flow today: £{abs(difference):.2f}** (risk-free profit)

At expiration the long call + bond position exactly offsets the short put + stock
return obligation in every scenario.
""")

with st.expander("Implied Option Values"):
    st.markdown(f"""
Based on the current inputs, parity implies the following fair values:

- **Implied Call Price:** £{C_implied:.2f} (market: £{C_market:.2f},
  difference: £{C_market - C_implied:+.2f})
- **Implied Put Price:** £{P_implied:.2f} (market: £{P_market:.2f},
  difference: £{P_market - P_implied:+.2f})

If an option's market price differs significantly from its implied value,
an arbitrage opportunity may exist (subject to transaction costs).
""")


# ---------------------------------------------------------------------------
# Section 4 – Synthetic Positions
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Synthetic Positions")

st.write(
    "Put-Call Parity can be rearranged to create **synthetic positions** that replicate "
    "one instrument using a combination of others. These are useful when certain instruments "
    "are illiquid, unavailable, or mispriced."
)

with st.expander("Synthetic Position Formulas", expanded=True):
    latex_synthetics = r"""
        \text{Synthetic Long Call:} \quad C = P + S_0 - K e^{-rT} \\
        \text{Synthetic Long Put:} \quad P = C + K e^{-rT} - S_0 \\
        \text{Synthetic Long Stock:} \quad S_0 = C - P + K e^{-rT} \\
        \text{Synthetic Forward:} \quad F_0 = S_0 - K e^{-rT} = C - P
        """
    st.code(latex_synthetics, language="latex")
    st.latex(latex_synthetics)

synthetic_type = st.selectbox(
    "Select a synthetic position to explore",
    [
        "Synthetic Long Call",
        "Synthetic Long Put",
        "Synthetic Long Stock",
        "Synthetic Forward",
    ],
    index=0,
    key="synth_select",
)

synth_details = {
    "Synthetic Long Call": {
        "formula": r"C = P + S_0 - K e^{-rT}",
        "components": [
            "Buy the put option",
            "Buy the underlying stock",
            "Borrow the present value of the strike (sell a bond)",
        ],
        "use_case": (
            "When call options are illiquid or relatively expensive compared to puts. "
            "This replicates the call's payoff exactly."
        ),
        "payoff": "max(S_T - K, 0)  — identical to a long call",
    },
    "Synthetic Long Put": {
        "formula": r"P = C + K e^{-rT} - S_0",
        "components": [
            "Buy the call option",
            "Lend the present value of the strike (buy a bond)",
            "Short the underlying stock",
        ],
        "use_case": (
            "When put options are illiquid or mispriced. Also useful in markets where "
            "puts are not available but calls are."
        ),
        "payoff": "max(K - S_T, 0)  — identical to a long put",
    },
    "Synthetic Long Stock": {
        "formula": r"S_0 = C - P + K e^{-rT}",
        "components": [
            "Buy the call option",
            "Sell the put option (same strike and expiry)",
            "Lend the present value of the strike (buy a bond)",
        ],
        "use_case": (
            "Create equity-like exposure without holding shares directly. "
            "Useful for gaining leveraged exposure or when share purchase is restricted."
        ),
        "payoff": "S_T  — identical to holding the stock",
    },
    "Synthetic Forward": {
        "formula": r"F_0 = C - P",
        "components": [
            "Buy the call option",
            "Sell the put option (same strike and expiry)",
        ],
        "use_case": (
            "Create forward contract exposure using options. The net premium "
            "(C - P) equals the present value of the forward price minus the strike."
        ),
        "payoff": "S_T - K  — identical to a long forward at strike K",
    },
}

info = synth_details[synthetic_type]

col_synth1, col_synth2 = st.columns(2)

with col_synth1:
    st.markdown("**Position Details**")
    st.latex(info["formula"])
    st.markdown(f"**Use Case:** {info['use_case']}")
    st.markdown(f"**Payoff at Expiration:** {info['payoff']}")

with col_synth2:
    st.markdown("**Construction**")
    for i, step in enumerate(info["components"], 1):
        st.markdown(f"{i}. {step}")


# ---------------------------------------------------------------------------
# Section 5 – Pre-Expiration Value Plot
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Pre-Expiration Portfolio Values")

st.write(
    "Before expiration, the risk-free rate, time to expiry, and volatility all affect "
    "option values. This plot uses the Black-Scholes model to price calls and puts "
    "and demonstrates that parity holds continuously — not just at expiration."
)

col_pre1, col_pre2, col_pre3 = st.columns(3)

with col_pre1:
    K_pre = st.slider(
        "Strike Price (K)",
        min_value=50.0,
        max_value=150.0,
        value=100.0,
        step=5.0,
        key="k_pre",
    )
    sigma_pre = (
        st.slider(
            "Volatility (σ %)",
            min_value=10,
            max_value=80,
            value=25,
            step=5,
            key="sigma_pre",
        )
        / 100
    )

with col_pre2:
    r_pre = (
        st.slider(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            key="r_pre",
        )
        / 100
    )
    T_pre = st.slider(
        "Time to Expiration (years)",
        min_value=0.1,
        max_value=2.0,
        value=1.0,
        step=0.1,
        key="t_pre",
    )

with col_pre3:
    show_components_pre = st.checkbox(
        "Show individual components",
        value=False,
        key="show_comp_pre",
    )

S_range = np.linspace(K_pre * 0.5, K_pre * 1.5, 200)

call_values = black_scholes_call(S_range, K_pre, T_pre, r_pre, sigma_pre)
put_values = black_scholes_put(S_range, K_pre, T_pre, r_pre, sigma_pre)
PV_K_pre = K_pre * np.exp(-r_pre * T_pre)

portfolio_A_pre = call_values + PV_K_pre
portfolio_B_pre = put_values + S_range

chart_col_pre, text_col_pre = st.columns([3, 2])

with chart_col_pre:
    fig2, ax2 = plt.subplots(figsize=(10, 6))

    if show_components_pre:
        ax2.plot(
            S_range, call_values, "b--", alpha=0.6, linewidth=1, label="Call Value (BS)"
        )
        ax2.plot(
            S_range, put_values, "r--", alpha=0.6, linewidth=1, label="Put Value (BS)"
        )
        ax2.axhline(
            y=PV_K_pre,
            color="orange",
            linestyle="--",
            alpha=0.6,
            linewidth=1,
            label=f"Bond PV(K) = £{PV_K_pre:.2f}",
        )
        ax2.plot(
            S_range,
            S_range,
            "g--",
            alpha=0.6,
            linewidth=1,
            label="Stock Value (S₀)",
        )

    ax2.plot(
        S_range,
        portfolio_A_pre,
        color="purple",
        linewidth=2.5,
        label="Portfolio A (Call + Bond)",
    )
    ax2.plot(
        S_range,
        portfolio_B_pre,
        color="teal",
        linewidth=2.5,
        linestyle="--",
        label="Portfolio B (Put + Stock)",
    )

    ax2.axvline(
        x=K_pre, color="grey", linestyle=":", alpha=0.5, label=f"Strike: £{K_pre:.0f}"
    )

    ax2.set_xlabel("Current Stock Price (S₀)", fontsize=12)
    ax2.set_ylabel("Portfolio Value", fontsize=12)
    ax2.set_title(
        f"Pre-Expiration Portfolio Values "
        f"(T={T_pre:.1f}y, r={r_pre * 100:.1f}%, σ={sigma_pre * 100:.0f}%)",
        fontsize=13,
        fontweight="bold",
    )
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig2)

with text_col_pre:
    st.markdown("#### Understanding Pre-Expiration Values")
    st.markdown("""
Both portfolio lines overlap perfectly across all stock prices, confirming that
put-call parity holds continuously throughout the option's life.

**Key observations:**
- Option values include both intrinsic and time value
- The risk-free rate affects the bond's present value (PV of K)
- Higher volatility increases both call and put values, but the parity still holds
- As T approaches 0, values converge to the at-expiration payoffs
""")

    idx_atm = np.argmin(np.abs(S_range - K_pre))
    st.markdown(f"""
**Sample values at S₀ = K (ATM):**
- Call value: £{call_values[idx_atm]:.2f}
- Put value: £{put_values[idx_atm]:.2f}
- Bond PV(K): £{PV_K_pre:.2f}
- Portfolio A: £{portfolio_A_pre[idx_atm]:.2f}
- Portfolio B: £{portfolio_B_pre[idx_atm]:.2f}
""")


# ---------------------------------------------------------------------------
# Section 6 – Assumptions and Limitations
# ---------------------------------------------------------------------------

st.markdown("---")

with st.expander("Assumptions and Limitations"):
    st.markdown("""
#### Assumptions Required for Put-Call Parity

Put-Call Parity holds under the following conditions:

1. **European options only** — cannot be exercised before expiration. American options
   violate parity because the early exercise premium creates an inequality.
2. **No dividends** — the underlying stock pays no dividends during the option's life.
   If dividends are expected, parity must be adjusted (see below).
3. **No transaction costs** — no commissions, bid-ask spreads, or market impact.
   In practice, small violations within transaction cost bounds are tolerated.
4. **No-arbitrage** — markets are efficient and arbitrage opportunities are
   quickly exploited.
5. **Continuous compounding** — the risk-free rate compounds continuously.
6. **Same strike and expiration** — the call and put must have identical
   strike prices and expiration dates.
7. **Frictionless markets** — no short-selling restrictions, and borrowing
   and lending occur at the same risk-free rate.

#### When Parity Breaks Down

- **American options:** The right to exercise early means
  $S_0 - K \\leq C_{\\text{Am}} - P_{\\text{Am}} \\leq S_0 - K e^{-rT}$ (bounds, not equality).
- **Dividends:** Expected dividends reduce call values and increase put values.
- **Transaction costs:** Bid-ask spreads create "no-arbitrage bands" around the
  theoretical parity relationship.
- **Borrowing constraints:** Different borrowing and lending rates weaken the
  arbitrage mechanism.
""")


# ---------------------------------------------------------------------------
# Section 7 – Dividend-Adjusted Parity
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Dividend-Adjusted Put-Call Parity")

st.write(
    "When the underlying stock pays dividends, put-call parity must be adjusted to "
    "account for the present value of expected dividends or a continuous dividend yield."
)

with st.expander("Dividend-Adjusted Formulas", expanded=False):
    latex_div = r"""
        \text{Discrete dividends:} \quad C + K e^{-rT} = P + S_0 - PV(D) \\ \\

        \text{Continuous dividend yield:} \quad C + K e^{-rT} = P + S_0 e^{-qT} \\ \\

        where: \\
        D = \text{known dividend payments during the option's life} \\
        PV(D) = \text{present value of those dividends} \\
        q = \text{continuous dividend yield}
        """
    st.code(latex_div, language="latex")
    st.latex(latex_div)

st.write(
    "**Intuition:** Holding the stock entitles you to receive dividends, but holding a "
    "call option does not. The right-hand side of the parity equation must therefore be "
    "reduced by the present value of the dividends the call holder misses out on."
)

st.markdown("##### Dividend Adjustment Example")

col_div1, col_div2 = st.columns(2)

with col_div1:
    S0_div = st.number_input(
        "Stock Price (S₀)", min_value=1.0, value=100.0, step=1.0, key="s0_div"
    )
    K_div = st.number_input(
        "Strike Price (K)", min_value=1.0, value=100.0, step=1.0, key="k_div"
    )
    C_div = st.number_input(
        "Call Price (C)", min_value=0.0, value=10.0, step=0.5, key="c_div"
    )

with col_div2:
    r_div = (
        st.slider(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            key="r_div",
        )
        / 100
    )
    T_div = st.slider(
        "Time to Expiration (years)",
        min_value=0.1,
        max_value=2.0,
        value=1.0,
        step=0.1,
        key="t_div",
    )
    q_div = (
        st.slider(
            "Continuous Dividend Yield (q %)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key="q_div",
        )
        / 100
    )

PV_K_div = K_div * np.exp(-r_div * T_div)
S_adj = S0_div * np.exp(-q_div * T_div)
P_implied_div = C_div + PV_K_div - S_adj
P_implied_no_div = C_div + PV_K_div - S0_div

col_divr1, col_divr2 = st.columns(2)

with col_divr1:
    st.metric(
        label="Dividend-Adjusted Stock Value",
        value=f"£{S_adj:.2f}",
        delta=f"£{S_adj - S0_div:.2f} from unadjusted",
    )
    st.metric(label="Present Value of Strike", value=f"£{PV_K_div:.2f}")

with col_divr2:
    st.metric(label="Implied Put (with dividends)", value=f"£{P_implied_div:.2f}")
    st.metric(label="Implied Put (without dividends)", value=f"£{P_implied_no_div:.2f}")

st.write(
    f"The continuous dividend yield of {q_div * 100:.1f}% reduces the effective stock "
    f"price from £{S0_div:.2f} to £{S_adj:.2f}, which **increases** the implied put "
    f"value by £{P_implied_div - P_implied_no_div:.2f} compared to the no-dividend case."
)


# ---------------------------------------------------------------------------
# Section 8 – Key Takeaways
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Key Takeaways")

col_take1, col_take2 = st.columns(2)

with col_take1:
    st.markdown("""
**Theoretical Importance:**
- Fundamental no-arbitrage relationship in options pricing
- Ensures consistent pricing between calls and puts
- Basis for constructing synthetic positions and hedging strategies
- Holds continuously, not just at expiration
""")

with col_take2:
    st.markdown("""
**Practical Applications:**
- Detect mispricing and identify arbitrage opportunities
- Create synthetic positions when instruments are illiquid
- Convert between calls and puts for hedging purposes
- Understand forward contract pricing via the options market
""")

st.info(
    "In practice, put-call parity violations are rare and short-lived due to active "
    "arbitrage by market makers. When deviations do occur they are typically small and "
    "fall within transaction cost bounds. Market makers continuously monitor parity to "
    "ensure consistent pricing across options markets."
)
