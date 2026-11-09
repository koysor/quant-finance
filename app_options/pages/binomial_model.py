import streamlit as st
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Union

from quant_finance.pricing.binomial import binomial_price
from quant_finance.pricing.black_scholes import black_scholes_price

st.set_page_config(
    page_title="The Binomial Model for Option Pricing", page_icon="📈", layout="wide"
)
st.header("The Binomial Model for Option Pricing")


st.info(
    "The binomial model is useful in learning about Options Pricing concepts "
    "because it shows a simplified step-by-step representation "
    "of the up-and-down movement on an underlying asset.  "
    "At the end of the binomial tree we know exactly what the option is worth in each possible future scenario. "
    "E.g. different share prices at expiry. "
    "We then work backwards through the tree, combining these possible payoffs with probabilities and discounting, "
    "to get a fair price for the option today."
)


st.write(
    "The Binomial Model is a **discrete-time model** for pricing options (as opposed to continuous time). "
    "It uses a **binomial tree** to represent the possible paths that the underlying asset price can take over time."
)
st.write(
    "The model assumes that the price of the underlying asset can move up or down by a certain factor in each time step, "
    "and it calculates the option price based on these possible future prices. \n"
    "- Up by a factor of **u** \n"
    "- Down by a factor of **d**"
)
st.write(
    "The Binomial Model: \n"
    "- Is particularly useful for pricing American options, which can be exercised at any time before expiration. \n"
    "- Is based on the principle of risk-neutral valuation, "
    "which assumes that investors are indifferent to risk and that the expected return on the underlying asset "
    "is equal to the risk-free rate."
)


def draw_one_step_binomial_tree(
    root_node: Tuple[Union[str, int], Union[str, int, float]],
    up_node: Tuple[Union[str, int], Union[str, int, float]],
    down_node: Tuple[Union[str, int], Union[str, int, float]],
    plot_title: str,
) -> None:
    root_node_label, root_node_value = root_node
    up_node_label, up_node_value = up_node
    down_node_label, down_node_value = down_node

    # Create the binomial tree graph
    G = nx.DiGraph()
    G.add_node(root_node_label, value=root_node_value)
    G.add_node(up_node_label, value=up_node_value)
    G.add_node(down_node_label, value=down_node_value)
    G.add_edge(root_node_label, up_node_label, move="Up")
    G.add_edge(root_node_label, down_node_label, move="Down")

    # Draw the graph
    pos = {root_node_label: (0, 0), up_node_label: (1, 1), down_node_label: (1, -1)}

    labels = nx.get_node_attributes(G, "value")
    edge_labels = nx.get_edge_attributes(G, "move")

    fig, ax = plt.subplots(figsize=(6, 4))
    nx.draw(
        G,
        pos,
        with_labels=False,
        node_color="lightblue",
        node_size=1_600,
        font_size=30,
        ax=ax,
    )
    nx.draw_networkx_labels(
        G, pos, labels={k: f"{k}\n{v}" for k, v in labels.items()}, font_size=7, ax=ax
    )
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_color="red", font_size=10, ax=ax
    )

    plt.title(plot_title)
    st.pyplot(fig)
    plt.close(fig)


st.subheader("Worked Example on a European Call Option")

st.write(
    "If we imagine a simple scenario where the underlying stock price on a Call Option can can only have "
    "one of two possible values after one time step, "
    "we can use the Binomial Model to calculate the value of the option. "
)


col1, col2 = st.columns(2)

with col1:
    price_initial = 100
    price_strike = 100
    price_up = st.number_input(
        "Up Price",
        min_value=101,
        max_value=110,
        value=101,
        step=1,
        help="The price of the underlying asset after an upward movement.",
    )
    price_down = st.number_input(
        "Down Price",
        min_value=90,
        max_value=99,
        value=99,
        step=1,
        help="The price of the underlying asset after a downward movement.",
    )

with col2:
    latex_code = rf"""
    \begin{{align*}}
        u &= \frac{{{price_up}}}{{{price_initial}}} \\
        ~ \\
        d &= \frac{{{price_down}}}{{{price_initial}}} \\
        ~ \\
        S_0 &= {price_initial} \\
        ~ \\
        S_u &= {price_up} \\
        ~ \\
        S_d &= {price_down} \\
        ~ \\
        K &= {price_strike} \\
    \end{{align*}}
    """
    st.latex(latex_code)


payoff_up = max(price_up - price_strike, 0)
payoff_down = max(price_down - price_strike, 0)

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Stock:")
    draw_one_step_binomial_tree(
        ("Initial Price", price_initial),
        ("Up", price_up),
        ("Down", price_down),
        "Stock Price Movement",
    )

with col2:
    st.markdown("##### Option:")
    draw_one_step_binomial_tree(
        (price_initial, ""),
        (price_up, f"Payoff: {payoff_up}"),
        (price_down, f"Payoff: {payoff_down}"),
        f"Call Option with Strike Price {price_strike}",
    )

st.write(
    f"If the stock price moves up to **{price_up}**, the value of the portfolio consisting of the **Option payoff** \
         and the **Short Stock Position** is:"
)
latex_code = rf"""{payoff_up} - \Delta * {price_up}"""
st.latex(latex_code)
st.write(
    "With $$\\Delta$$ being the number of shares of the underlying stock to Short."
)
st.write(
    f"If the stock price moves down to **{price_down}**, the value of the portfolio is:"
)
latex_code = rf"""{payoff_down} - \Delta * {price_down}"""
st.latex(latex_code)


st.subheader("Delta Neutral Hedging")

st.write(
    "In order to hedge the option, we need to create a portfolio that is delta neutral. "
    "This means that the portfolio's value does not change whether the Underlying Stock Price goes up or down. "
    "In order to do this we need to sell a certain number of shares of the underlying stock. "
)
st.write(
    "To determine $$\\Delta$$, the amount of the stock to Short, "
    "we equate the value of the portfolio after an upward movement to the value of the portfolio after a downward movement. "
)
latex_code = rf"""
\begin{{align*}}
    {payoff_up} - \Delta * {price_up} &= {payoff_down} - \Delta * {price_down} \\
    ~ \\
    {payoff_up} - {payoff_down} &= \Delta * {price_up} - \Delta * {price_down} \\
    ~ \\
    {payoff_up - payoff_down} &= \Delta * ({price_up} - {price_down}) \\
    ~ \\
    \Delta &= \frac{{{payoff_up - payoff_down}}}{{{price_up} - {price_down}}} \\
    ~ \\
    \Delta &= \frac{{{payoff_up - payoff_down}}}{{{price_up - price_down}}} \\
\end{{align*}}
"""
st.latex(latex_code)

st.info("""
- We do not care about whether the stock price goes up or down, as long as we have the right amount of shares to short.
- The value of the portfolio after an upward movement is equal to the value of the portfolio after a downward movement.
- The value of the portfolio is the same in both cases, which means that we have created a delta neutral portfolio.
- The probability of the stock price going up or down does not matter, as we are creating a delta neutral portfolio.
""")

st.warning("""
Note that interest rates are assumed to be zero in this example.
This is a simplification for the sake of clarity. With a rate r, the riskless portfolio's value at expiry \
would be discounted back to today rather than carried over unchanged.""")


st.subheader("Pricing the Option")

delta = (payoff_up - payoff_down) / (price_up - price_down)
portfolio_at_expiry = payoff_up - delta * price_up
option_price = portfolio_at_expiry + delta * price_initial
q_up = (price_initial - price_down) / (price_up - price_down)

st.write(
    "The hedged portfolio is worth the same whichever way the stock moves, so it is riskless. "
    "With a zero interest rate a riskless portfolio must be worth the same today as at expiry, "
    "otherwise there would be an arbitrage. That fixes the option price today:"
)
latex_code = rf"""
\begin{{align*}}
    \Pi_T &= {payoff_up} - {delta:.4f} \times {price_up} = {portfolio_at_expiry:.4f} \\
    ~ \\
    V_0 - \Delta S_0 &= \Pi_T \\
    ~ \\
    V_0 &= {portfolio_at_expiry:.4f} + {delta:.4f} \times {price_initial} = {option_price:.4f}
\end{{align*}}
"""
st.code(latex_code, language="latex")
st.latex(latex_code)

st.write(
    "The same price comes from the **risk-neutral probability** $q$: the probability of an up move that "
    "makes the stock's expected return equal the risk-free rate (zero here). The option price is then its "
    "expected payoff under $q$, discounted at the risk-free rate."
)
latex_code = rf"""
\begin{{align*}}
    q &= \frac{{S_0 - S_d}}{{S_u - S_d}} = \frac{{{price_initial} - {price_down}}}{{{price_up} - {price_down}}}
       = {q_up:.4f} \\
    ~ \\
    V_0 &= q \times {payoff_up} + (1 - q) \times {payoff_down} = {q_up * payoff_up + (1 - q_up) * payoff_down:.4f}
\end{{align*}}
"""
st.code(latex_code, language="latex")
st.latex(latex_code)

st.info(
    "The real-world probability of an up move never appears. Investors who disagree about it must still "
    "agree on the option price, because the option can be replicated with the stock. Here $q$ is a valid "
    "probability (between 0 and 1) because $S_d < S_0 < S_u$; if the stock could only rise, or only fall, "
    "relative to cash, there would be an arbitrage."
)


with st.expander("Binomial Model Assumptions"):
    st.write(
        "1. Over each time step the underlying price moves up by a factor u or down by a factor d."
    )
    st.write(
        "2. There is no arbitrage: $d < e^{r \\Delta t} < u$, so the stock neither always beats nor "
        "always trails the risk-free asset."
    )
    st.write(
        "3. Fractional trading and short selling are permitted, with no transaction costs or taxes."
    )
    st.write("4. The risk-free rate is constant over the life of the option.")
    st.write(
        "5. Trading takes place only at discrete time steps, and the option is valued at each node of the tree."
    )
    st.write(
        "6. With the Cox-Ross-Rubinstein choice $u = e^{\\sigma \\sqrt{\\Delta t}}$, $d = 1/u$, the "
        "distribution of the price at expiry tends to a lognormal as the number of steps grows, and the "
        "option price converges to the Black-Scholes price. A one-step tree is not lognormal."
    )
    st.write(
        "The model can also price American options, by checking at each node whether exercising "
        "immediately is worth more than continuing."
    )


st.subheader("From One Step to Many: the Cox-Ross-Rubinstein Model")

st.write(
    "Splitting the time to expiry into many small steps, and working backwards through the tree one step at "
    "a time, gives a price that converges to the Black-Scholes price for a European option. For an American "
    "option, each node takes the larger of the continuation value and the value of exercising there."
)

col1, col2, col3 = st.columns(3)
with col1:
    crr_spot = st.number_input("Stock Price (S)", min_value=1.0, value=100.0, step=1.0)
    crr_strike = st.number_input("Strike (K)", min_value=1.0, value=100.0, step=1.0)
    option_type = st.radio("Option Type", ["put", "call"], horizontal=True)
with col2:
    crr_expiry = st.slider("Time to Expiry (years)", 0.1, 3.0, 1.0, 0.1)
    crr_sigma = st.slider("Volatility (σ, %)", 5, 80, 20) / 100
with col3:
    crr_rate = st.slider("Risk-free Rate (r, %)", 0.0, 10.0, 5.0, 0.25) / 100
    crr_dividend = st.slider("Dividend Yield (q, %)", 0.0, 10.0, 0.0, 0.25) / 100
    max_steps = st.slider("Maximum Number of Steps", 10, 300, 100, 10)


def tree_price(n_steps: int, american: bool) -> float:
    """CRR price, or NaN when the tree is too coarse to be arbitrage-free."""
    try:
        return binomial_price(
            crr_spot,
            crr_strike,
            crr_expiry,
            crr_rate,
            crr_sigma,
            n_steps,
            option_type,
            american=american,
            q=crr_dividend,
        )
    except ValueError:
        return float("nan")


steps = np.arange(1, max_steps + 1)
european = np.array([tree_price(n, american=False) for n in steps])
american = np.array([tree_price(n, american=True) for n in steps])
bs_price = float(
    black_scholes_price(
        crr_spot, crr_strike, crr_expiry, crr_rate, crr_sigma, crr_dividend, option_type
    )
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(steps, european, label="CRR European", linewidth=1)
ax.plot(steps, american, label="CRR American", linewidth=1)
ax.axhline(bs_price, color="black", linestyle="--", label="Black-Scholes (European)")
ax.set_xlabel("Number of Steps")
ax.set_ylabel(f"{option_type.capitalize()} Price")
ax.set_title("Binomial Price against the Number of Steps")
ax.legend()
ax.grid(True, alpha=0.3)

chart_col, metric_col = st.columns([3, 1])
with chart_col:
    st.pyplot(fig)
    plt.close(fig)
with metric_col:
    st.metric("Black-Scholes", f"£{bs_price:.4f}")
    st.metric(f"CRR European ({max_steps} steps)", f"£{european[-1]:.4f}")
    st.metric(f"CRR American ({max_steps} steps)", f"£{american[-1]:.4f}")
    st.metric("Early Exercise Premium", f"£{american[-1] - european[-1]:.4f}")

if np.isnan(european).any():
    st.caption(
        "Missing points are trees with too few steps to satisfy d < exp((r − q)Δt) < u."
    )

st.write(
    "The European price oscillates around the Black-Scholes price and the error shrinks roughly in "
    "proportion to 1 / steps. An American put is worth more than a European put when early exercise pays: "
    "deep in the money, the interest earned on the strike received now outweighs the remaining time value. "
    "With no dividends, early exercise of an American call is never optimal, so its price equals the European one."
)

st.caption(
    "Cox, J.C., Ross, S.A. & Rubinstein, M. (1979). 'Option Pricing: A Simplified Approach.' "
    "Journal of Financial Economics, 7(3), 229–263. | "
    "Black, F. & Scholes, M. (1973). 'The Pricing of Options and Corporate Liabilities.' "
    "Journal of Political Economy, 81(3), 637–654."
)
