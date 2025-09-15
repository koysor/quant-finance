import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt


st.set_page_config(layout="wide")
st.markdown("### The Binomial Model for Option Pricing")


st.write(
    "The Binomial Model is a **discrete-time model** for pricing options (as opposed to continuous time). It uses a **binomial tree** to represent the possible paths that the underlying asset price can take over time."
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
    "- Is based on the principle of risk-neutral valuation, which assumes that investors are indifferent to risk and that the expected return on the underlying asset is equal to the risk-free rate."
)


def draw_one_step_binomial_tree(
    root_node: tuple, up_node: tuple, down_node: tuple, plot_title: str
):
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


st.markdown("### Worked Example on a European Call Option")

st.write(
    "If we imagine a simple scenario where the underlying stock price on a Call Option can can only have "
    "one of two possible values after one time step, we can use the Binomial Model to calculate the value of the option. "
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
        ("100", ""),
        (price_up, f"Payoff: {max(price_up - price_strike, 0)}"),
        (price_down, f"Payoff: {max(price_down - price_strike, 0)}"),
        f"Call Option with Strike Price {price_strike}",
    )

st.write(
    f"If the stock prices moves up to **{price_up}**, the the value of the portfolio consisting of the **Option payoff** \
         and the **Short Stock Position** is:"
)
latex_code = rf"""1 - \Delta * {price_up}"""
st.latex(latex_code)
st.write(
    "With $$\\Delta$$ being the number of shares of the underlying stock to Short."
)
st.write(
    f"If the stock prices moves down to **{price_down}**, the the value of the portfolio is:"
)
latex_code = rf"""0 - \Delta * {price_down}"""
st.latex(latex_code)


st.markdown("### Delta Neutral Hedging")

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
    1 - \Delta * {price_up} &= 0 - \Delta * {price_down} \\
    ~ \\
    1 &= \Delta * {price_up} - \Delta * {price_down} \\
    ~ \\
    1 &= \Delta * ({price_up} - {price_down}) \\
    ~ \\
    \Delta &= \frac{{1}}{{{price_up} - {price_down}}} \\
    ~ \\
    \Delta &= \frac{{1}}{{{price_up - price_down}}} \\
\end{{align*}}
"""
st.latex(latex_code)

st.info(
    """
- We do not care about whether the stock price goes up or down, as long as we have the right amount of shares to short.
- The value of the portfolio after an upward movement is equal to the value of the portfolio after a downward movement.
- The value of the portfolio is the same in both cases, which means that we have created a delta neutral portfolio.
- The probability of the stock price going up or down does not matter, as we are creating a delta neutral portfolio.
"""
)

st.warning(
    """
Note that interest rates are assumed to be zero in this example.
This is a simplification for the sake of clarity. In practice, interest rates would affect the present value of the option \
and the underlying asset."""
)


with st.expander("Binomial Model Assumptions"):
    st.write(
        "1. The underlying asset price can move up or down to one of two possible prices in each time step."
    )
    st.write("2. Fractional trading is permitted.")
    st.write("2. The risk-free rate is constant over the life of the option.")
    st.write(
        "3. The option can be exercised at any time before expiration (for American options)."
    )
    st.write(
        "4. The model assumes that the option price is calculated at specific discrete time intervals."
    )
    st.write(
        "5. The model assumes that the underlying asset price follows a random walk, which means that the future price is uncertain and can move in any direction."
    )
    st.write(
        "6. The model assumes that the underlying asset price follows a lognormal distribution, which means that the logarithm of the price follows a normal distribution."
    )
    st.write(
        "7. The model assumes that the option price is a function of the underlying asset price, the strike price, the time to expiration, and the risk-free rate."
    )
