import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Modern Portfolio Theory - Efficient Frontier",
    page_icon="💼",
    layout="wide",
)
st.header("Modern Portfolio Theory - Efficient Frontier")

st.write(
    "Modern Portfolio Theory (MPT), developed by Harry Markowitz in 1952, demonstrates how "
    "investors can construct portfolios to maximise expected return for a given level of risk. "
    "The key insight is that diversification can reduce portfolio risk without sacrificing returns."
)

st.info(
    "The efficient frontier shows all portfolios that offer the highest expected return "
    "for each level of risk. Portfolios below the frontier are suboptimal because you could "
    "achieve higher returns for the same risk, or lower risk for the same return."
)


st.markdown("#### Two-Asset Portfolio Mathematics")

st.write(
    "For a portfolio of two assets with weights $w_1$ and $w_2$ (where $w_1 + w_2 = 1$), "
    "the portfolio return and risk are calculated as follows:"
)

with st.expander(label="Portfolio Return", expanded=True):
    latex_return = r"""
        R_p = w_1 R_1 + w_2 R_2 \\ \\

        where: \\
        R_p = \text{portfolio expected return} \\
        w_1, w_2 = \text{weights of assets 1 and 2} \\
        R_1, R_2 = \text{expected returns of assets 1 and 2}
        """
    st.code(latex_return, language="latex")
    st.latex(latex_return)

st.write(
    "The portfolio return is simply the weighted average of the individual asset returns. "
    "However, portfolio risk is more complex due to the interaction between assets."
)

with st.expander(label="Portfolio Variance (Risk)", expanded=True):
    latex_variance = r"""
        \sigma_p^2 = w_1^2 \sigma_1^2 + w_2^2 \sigma_2^2 + 2 w_1 w_2 \sigma_1 \sigma_2 \rho_{12} \\ \\

        where: \\
        \sigma_p^2 = \text{portfolio variance} \\
        \sigma_1, \sigma_2 = \text{standard deviations of assets 1 and 2} \\
        \rho_{12} = \text{correlation between assets 1 and 2}
        """
    st.code(latex_variance, language="latex")
    st.latex(latex_variance)

st.write(
    "The correlation term $\\rho_{12}$ is crucial. When assets are not perfectly correlated "
    "($\\rho < 1$), the portfolio risk is **less than** the weighted average of individual risks. "
    "This is the mathematical basis for the diversification benefit."
)


st.markdown("#### Interactive Efficient Frontier")

st.write(
    "Adjust the parameters below to see how the efficient frontier changes with different "
    "asset characteristics and correlations."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Asset 1**")
    r1 = st.slider(
        "Expected Return (%)",
        min_value=0.0,
        max_value=30.0,
        value=8.0,
        step=0.5,
        key="r1",
    )
    sigma1 = st.slider(
        "Volatility (%)",
        min_value=1.0,
        max_value=50.0,
        value=15.0,
        step=0.5,
        key="sigma1",
    )

with col2:
    st.markdown("**Asset 2**")
    r2 = st.slider(
        "Expected Return (%)",
        min_value=0.0,
        max_value=30.0,
        value=14.0,
        step=0.5,
        key="r2",
    )
    sigma2 = st.slider(
        "Volatility (%)",
        min_value=1.0,
        max_value=50.0,
        value=25.0,
        step=0.5,
        key="sigma2",
    )

with col3:
    st.markdown("**Correlation**")
    rho = st.slider(
        "Correlation (ρ)",
        min_value=-1.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        key="rho",
    )
    st.write("")
    st.write(
        f"ρ = {rho:.2f}: "
        + (
            "Perfect positive correlation"
            if rho == 1.0
            else (
                "Perfect negative correlation"
                if rho == -1.0
                else (
                    "No correlation"
                    if rho == 0.0
                    else ("Positive correlation" if rho > 0 else "Negative correlation")
                )
            )
        )
    )

# Convert percentages to decimals
r1_dec = r1 / 100
r2_dec = r2 / 100
sigma1_dec = sigma1 / 100
sigma2_dec = sigma2 / 100

# Generate portfolio combinations
weights = np.linspace(0, 1, 100)
portfolio_returns = []
portfolio_risks = []

for w1 in weights:
    w2 = 1 - w1
    # Portfolio return
    port_return = w1 * r1_dec + w2 * r2_dec
    # Portfolio variance
    port_variance = (
        (w1**2) * (sigma1_dec**2)
        + (w2**2) * (sigma2_dec**2)
        + 2 * w1 * w2 * sigma1_dec * sigma2_dec * rho
    )
    port_risk = np.sqrt(port_variance)

    portfolio_returns.append(port_return * 100)
    portfolio_risks.append(port_risk * 100)

# Find minimum variance portfolio
# Analytical solution for two assets
if sigma1_dec != sigma2_dec or rho != 1:
    w1_min_var = (sigma2_dec**2 - sigma1_dec * sigma2_dec * rho) / (
        sigma1_dec**2 + sigma2_dec**2 - 2 * sigma1_dec * sigma2_dec * rho
    )
    w1_min_var = np.clip(w1_min_var, 0, 1)
else:
    w1_min_var = 0.5

w2_min_var = 1 - w1_min_var
min_var_return = (w1_min_var * r1_dec + w2_min_var * r2_dec) * 100
min_var_risk = (
    np.sqrt(
        (w1_min_var**2) * (sigma1_dec**2)
        + (w2_min_var**2) * (sigma2_dec**2)
        + 2 * w1_min_var * w2_min_var * sigma1_dec * sigma2_dec * rho
    )
    * 100
)

# Create visualisation
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the efficient frontier
ax.plot(
    portfolio_risks,
    portfolio_returns,
    "b-",
    linewidth=2,
    label="Portfolio Combinations",
)

# Mark individual assets
ax.scatter([sigma1], [r1], color="red", s=150, zorder=5, label="Asset 1 (w₁=100%)")
ax.scatter([sigma2], [r2], color="green", s=150, zorder=5, label="Asset 2 (w₂=100%)")

# Mark minimum variance portfolio
ax.scatter(
    [min_var_risk],
    [min_var_return],
    color="orange",
    s=200,
    marker="*",
    zorder=5,
    label=f"Min Variance (w₁={w1_min_var:.0%})",
)

# Add labels
ax.set_xlabel("Portfolio Risk (Standard Deviation) %", fontsize=12)
ax.set_ylabel("Expected Return %", fontsize=12)
ax.set_title("Efficient Frontier - Two Asset Portfolio", fontsize=14)
ax.legend(loc="upper left")
ax.grid(True, alpha=0.3)

# Set axis limits with some padding
x_min = max(0, min(portfolio_risks) - 2)
x_max = max(portfolio_risks) + 2
y_min = max(0, min(portfolio_returns) - 1)
y_max = max(portfolio_returns) + 1
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

plt.tight_layout()
st.pyplot(fig)


st.markdown("#### Portfolio Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Asset 1**")
    st.metric("Expected Return", f"{r1:.1f}%")
    st.metric("Volatility", f"{sigma1:.1f}%")

with col2:
    st.markdown("**Asset 2**")
    st.metric("Expected Return", f"{r2:.1f}%")
    st.metric("Volatility", f"{sigma2:.1f}%")

with col3:
    st.markdown("**Minimum Variance Portfolio**")
    st.metric("Weight in Asset 1", f"{w1_min_var:.1%}")
    st.metric("Expected Return", f"{min_var_return:.2f}%")
    st.metric("Volatility", f"{min_var_risk:.2f}%")


st.markdown("#### The Diversification Benefit")

# Calculate what the risk would be without diversification (weighted average)
weighted_avg_risk = w1_min_var * sigma1 + w2_min_var * sigma2
diversification_benefit = weighted_avg_risk - min_var_risk

st.write(
    f"At the minimum variance portfolio, if there were no diversification benefit "
    f"(i.e., if ρ = 1), the portfolio risk would be the weighted average: "
    f"**{weighted_avg_risk:.2f}%**."
)
st.write(
    f"Due to imperfect correlation (ρ = {rho:.2f}), the actual portfolio risk is "
    f"**{min_var_risk:.2f}%**, a reduction of **{diversification_benefit:.2f}%**."
)

if rho < 1:
    st.success(
        f"Diversification benefit: {diversification_benefit:.2f} percentage points "
        f"of risk reduction"
    )
else:
    st.warning(
        "With perfect correlation (ρ = 1), there is no diversification benefit. "
        "The efficient frontier becomes a straight line between the two assets."
    )


st.markdown("#### Key Insights")

st.write("""
**Understanding the Efficient Frontier:**
- The curve shows all possible risk-return combinations achievable by varying portfolio weights
- The upper portion of the curve (from minimum variance upward) is the "efficient frontier"
- Rational investors should only hold portfolios on the efficient frontier

**Impact of Correlation:**
- When ρ = 1: The frontier is a straight line (no diversification benefit)
- When ρ = 0: Significant risk reduction is possible through diversification
- When ρ = -1: Perfect hedging is possible; minimum variance can reach zero risk

**Practical Implications:**
- Seek assets with low or negative correlations to maximise diversification benefits
- Even modest correlation reductions can significantly improve portfolio efficiency
- The minimum variance portfolio is not necessarily optimal; it depends on risk tolerance
""")

st.caption(
    "Markowitz, H. (1952). 'Portfolio Selection.' The Journal of Finance, 7(1), 77–91."
)
