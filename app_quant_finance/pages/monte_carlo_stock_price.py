import streamlit as st
import numpy as np
import matplotlib.pyplot as plt


st.set_page_config(layout="wide")
st.markdown("### Monte Carlo Simulation - Stock Price Random Walk")

st.write(
    "Monte Carlo simulation uses random sampling to model the probability of different outcomes in financial markets. "
    "For stock prices, we simulate multiple possible price paths using geometric Brownian motion."
)

st.markdown("#### Geometric Brownian Motion Model")

st.write(
    "Stock prices are commonly modeled using geometric Brownian motion, which assumes that stock returns "
    "follow a normal distribution. The stock price evolution is given by:"
)

latex_code = r"""
dS_t = \mu S_t dt + \sigma S_t dW_t
"""
st.code(latex_code, language="latex")
st.latex(latex_code)

st.write("Where:")
st.write("- $S_t$ is the stock price at time $t$")
st.write("- $\\mu$ is the expected return (drift)")
st.write("- $\\sigma$ is the volatility")
st.write("- $dW_t$ is a Wiener process (random walk)")

st.write("The discrete approximation for simulation is:")
latex_discrete = r"""
S_{t+\Delta t} = S_t \exp\left((\mu - \frac{\sigma^2}{2})\Delta t + \sigma \sqrt{\Delta t} Z\right)
"""
st.latex(latex_discrete)
st.write("Where $Z \\sim N(0,1)$ is a standard normal random variable.")

st.markdown("#### Interactive Monte Carlo Simulation")


col1, col2 = st.columns(2)

with col1:
    # Input parameters
    S0 = st.number_input(
        "Initial Stock Price (£)", min_value=1.0, value=100.0, step=1.0
    )
    mu = st.number_input(
        "Expected Annual Return (μ)",
        min_value=-1.0,
        max_value=1.0,
        value=0.1,
        step=0.01,
        format="%.3f",
    )
    sigma = st.number_input(
        "Annual Volatility (σ)",
        min_value=0.01,
        max_value=2.0,
        value=0.2,
        step=0.01,
        format="%.3f",
    )

with col2:
    T = st.number_input(
        "Time Horizon (Years)", min_value=0.1, max_value=5.0, value=1.0, step=0.1
    )
    n_steps = st.number_input(
        "Number of Time Steps", min_value=50, max_value=1000, value=252, step=1
    )
    n_simulations = st.number_input(
        "Number of Simulations", min_value=1, max_value=10000, value=1000, step=100
    )

# Generate Monte Carlo simulations
if st.button("Run Monte Carlo Simulation"):
    # Time parameters
    dt = T / n_steps
    t = np.linspace(0, T, n_steps + 1)

    # Initialize price matrix
    prices = np.zeros((n_simulations, n_steps + 1))
    prices[:, 0] = S0

    # Generate random numbers
    np.random.seed(42)  # For reproducibility
    random_shocks = np.random.normal(0, 1, (n_simulations, n_steps))

    # Simulate price paths
    for i in range(n_steps):
        prices[:, i + 1] = prices[:, i] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * random_shocks[:, i]
        )

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Sample of price paths
    sample_size = min(100, n_simulations)
    sample_indices = np.random.choice(n_simulations, sample_size, replace=False)

    for idx in sample_indices:
        ax1.plot(t, prices[idx, :], alpha=0.3, linewidth=0.8, color="steelblue")

    # Highlight mean path
    mean_path = np.mean(prices, axis=0)
    ax1.plot(t, mean_path, color="red", linewidth=2, label="Mean Path")
    ax1.plot(
        t,
        S0 * np.exp(mu * t),
        color="green",
        linewidth=2,
        linestyle="--",
        label="Theoretical Mean",
    )

    ax1.set_xlabel("Time (Years)")
    ax1.set_ylabel("Stock Price (£)")
    ax1.set_title(
        f"Monte Carlo Stock Price Simulation\n({sample_size} sample paths shown)"
    )
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Final price distribution
    final_prices = prices[:, -1]
    ax2.hist(
        final_prices,
        bins=50,
        alpha=0.7,
        color="lightblue",
        edgecolor="black",
        density=True,
    )
    ax2.axvline(
        np.mean(final_prices),
        color="red",
        linestyle="-",
        linewidth=2,
        label=f"Mean: £{np.mean(final_prices):.2f}",
    )
    ax2.axvline(
        np.median(final_prices),
        color="orange",
        linestyle="--",
        linewidth=2,
        label=f"Median: £{np.median(final_prices):.2f}",
    )

    ax2.set_xlabel("Final Stock Price (£)")
    ax2.set_ylabel("Probability Density")
    ax2.set_title(f"Distribution of Final Stock Prices\n(After {T} years)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)

    # Display statistics
    st.markdown("#### Simulation Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Mean Final Price", f"£{np.mean(final_prices):.2f}")
        st.metric("Median Final Price", f"£{np.median(final_prices):.2f}")

    with col2:
        st.metric("Standard Deviation", f"£{np.std(final_prices):.2f}")
        st.metric("Min Price", f"£{np.min(final_prices):.2f}")

    with col3:
        st.metric("Max Price", f"£{np.max(final_prices):.2f}")
        theoretical_mean = S0 * np.exp(mu * T)
        st.metric("Theoretical Mean", f"£{theoretical_mean:.2f}")

    # Risk metrics
    st.markdown("#### Risk Analysis")

    returns = (final_prices - S0) / S0
    prob_loss = np.sum(final_prices < S0) / n_simulations * 100
    var_95 = np.percentile(final_prices, 5)
    var_99 = np.percentile(final_prices, 1)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Probability of Loss", f"{prob_loss:.1f}%")
        st.metric("Value at Risk (95%)", f"£{var_95:.2f}")

    with col2:
        st.metric("Value at Risk (99%)", f"£{var_99:.2f}")
        st.metric("Expected Return", f"{np.mean(returns) * 100:.2f}%")

st.markdown("#### Key Insights")

st.write(
    """
**Monte Carlo Simulation Properties:**
- Each simulation generates random price paths based on the specified parameters
- The mean of all simulations converges to the theoretical expected value
- Higher volatility creates wider distributions of final prices
- More simulations provide more accurate statistical estimates

**Risk Management Applications:**
- **Value at Risk (VaR):** Shows potential losses at different confidence levels
- **Scenario Analysis:** Understand range of possible outcomes
- **Portfolio Optimization:** Compare risk-return profiles of different assets
- **Option Pricing:** Foundation for more complex derivatives pricing models
"""
)
