import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Martingales", page_icon="🎲", layout="wide")
st.header("Martingales")

st.write(
    "In probability theory, a **Martingale** is a sequence of random variables where, "
    "at any given time, the conditional expectation of the next value in the sequence, "
    "given all prior values, is equal to the current value."
)

st.latex(r"E[X_{n+1} | X_1, X_2, \dots, X_n] = X_n")

st.write(
    "Intuitively, a martingale models a 'fair game' where there is no drift or trend. "
    "If you are playing a fair game, your expected wealth after the next round is exactly "
    "what you have now, regardless of your past wins or losses."
)

st.markdown("#### The Symmetric Random Walk")
st.write(
    "A simple example of a martingale is a symmetric random walk. "
    "Suppose you start with an initial wealth $X_0$ and in each step you either win £1 or lose £1 "
    "with equal probability (0.5)."
)

col1, col2 = st.columns(2)

with col1:
    initial_wealth = st.number_input(
        "Initial Wealth (£)", min_value=0.0, value=100.0, step=10.0
    )
    n_steps = st.slider("Number of Steps", min_value=10, max_value=1000, value=100)

with col2:
    n_simulations = st.slider(
        "Number of Simulations", min_value=1, max_value=500, value=50
    )
    win_prob = st.slider(
        "Probability of Winning (p)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        help="A value of 0.5 makes it a Martingale. >0.5 is a Sub-Martingale, <0.5 is a Super-Martingale.",
    )

if st.button("Run Simulation"):
    # Generate random steps: +1 with prob p, -1 with prob 1-p
    steps = np.random.choice(
        [1, -1], size=(n_simulations, n_steps), p=[win_prob, 1 - win_prob]
    )

    # Calculate paths by taking cumulative sum
    paths = np.zeros((n_simulations, n_steps + 1))
    paths[:, 0] = initial_wealth
    paths[:, 1:] = initial_wealth + np.cumsum(steps, axis=1)

    time = np.arange(n_steps + 1)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot individual paths
    for i in range(n_simulations):
        ax.plot(time, paths[i, :], alpha=0.3, linewidth=1)

    # Plot average path
    average_path = np.mean(paths, axis=0)
    ax.plot(time, average_path, color="red", linewidth=3, label="Average Path")

    # Plot theoretical expectation
    # E[X_n] = X_0 + n * (2p - 1)
    theoretical_expectation = initial_wealth + time * (2 * win_prob - 1)
    ax.plot(
        time,
        theoretical_expectation,
        color="black",
        linestyle="--",
        linewidth=2,
        label="Theoretical Expectation",
    )

    ax.set_xlabel("Steps")
    ax.set_ylabel("Wealth (£)")
    ax.set_title(f"Random Walk Simulation (p={win_prob})")
    ax.legend()
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    final_avg = average_path[-1]
    m1.metric("Final Average Wealth", f"£{final_avg:.2f}")
    m2.metric("Expected Wealth", f"£{theoretical_expectation[-1]:.2f}")
    m3.metric("Difference", f"£{final_avg - theoretical_expectation[-1]:.2f}")

    if win_prob == 0.5:
        st.success(
            "This is a **Martingale** (Fair Game). The expected value remains constant."
        )
    elif win_prob > 0.5:
        st.info("This is a **Sub-Martingale**. The expected value increases over time.")
    else:
        st.warning(
            "This is a **Super-Martingale**. The expected value decreases over time."
        )

st.markdown("#### Martingales in Finance")
st.write("""
    In the context of efficient markets, discounted asset prices are often modeled as martingales 
    under a **risk-neutral probability measure**. This is a fundamental concept in derivative pricing, 
    such as the Black-Scholes model.
    
    Key properties include:
    - **No-Arbitrage:** If prices are martingales, there are no risk-free profit opportunities.
    - **Unbiasedness:** The current price is the best predictor of future prices (under the risk-neutral measure).
    - **Stopping Time Theorem:** You cannot increase your expected wealth by choosing when to stop playing a martingale.
    """)

st.caption("Doob, J. L. (1953). 'Stochastic Processes.' John Wiley & Sons.")
