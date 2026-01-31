import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.markdown("### Capital Asset Pricing Model (CAPM)")

st.write(
    "The Capital Asset Pricing Model, developed by William Sharpe (1964), John Lintner (1965), "
    "and Jan Mossin (1966), describes the relationship between systematic risk and expected "
    "return for assets. It builds upon Modern Portfolio Theory to show that the expected return "
    "of an asset is determined by its sensitivity to market risk (beta)."
)

st.info(
    "CAPM's key insight is that investors should only be compensated for systematic (market) "
    "risk, not for unsystematic (idiosyncratic) risk, because unsystematic risk can be "
    "diversified away by holding a well-diversified portfolio."
)


st.markdown("#### The CAPM Equation")

st.write("The expected return of an asset according to CAPM is given by:")

with st.expander(label="CAPM Formula", expanded=True):
    latex_capm = r"""
        E(R_i) = R_f + \beta_i (E(R_m) - R_f) \\ \\

        where: \\
        E(R_i) = \text{expected return of asset } i \\
        R_f = \text{risk-free rate} \\
        \beta_i = \text{beta of asset } i \\
        E(R_m) = \text{expected return of the market} \\
        E(R_m) - R_f = \text{market risk premium}
        """
    st.code(latex_capm, language="latex")
    st.latex(latex_capm)

st.write(
    "The term $\\beta_i (E(R_m) - R_f)$ represents the risk premium for holding asset $i$. "
    "Assets with higher beta have higher expected returns because they carry more systematic risk."
)


st.markdown("#### Understanding Beta")

with st.expander(label="Beta Formula", expanded=True):
    latex_beta = r"""
        \beta_i = \frac{Cov(R_i, R_m)}{Var(R_m)} = \frac{\sigma_{i,m}}{\sigma_m^2} \\ \\

        where: \\
        Cov(R_i, R_m) = \text{covariance of asset returns with market returns} \\
        Var(R_m) = \text{variance of market returns}
        """
    st.code(latex_beta, language="latex")
    st.latex(latex_beta)

st.write("""
**Interpreting Beta:**
- **β = 1**: Asset moves with the market (e.g., index funds)
- **β > 1**: Asset is more volatile than the market (e.g., growth stocks, tech)
- **β < 1**: Asset is less volatile than the market (e.g., utilities, consumer staples)
- **β = 0**: Asset has no correlation with market (e.g., risk-free asset)
- **β < 0**: Asset moves opposite to market (rare, e.g., some gold stocks)
""")


st.markdown("#### The Security Market Line (SML)")

st.write(
    "The Security Market Line is a graphical representation of CAPM. It plots expected return "
    "against beta, showing the linear relationship between systematic risk and return. "
    "All fairly priced assets should lie on the SML."
)

st.write(
    "Adjust the parameters below to see how the SML changes and how individual assets "
    "compare to their CAPM-predicted returns."
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Market Parameters**")
    risk_free_rate = st.slider(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=3.0,
        step=0.25,
        key="rf",
    )
    market_return = st.slider(
        "Expected Market Return (%)",
        min_value=0.0,
        max_value=20.0,
        value=10.0,
        step=0.5,
        key="rm",
    )

with col2:
    st.markdown("**Sample Assets**")
    st.write("Add assets to plot on the SML:")

    # Define some sample assets with beta and actual return
    assets = {
        "Market Portfolio": {"beta": 1.0, "actual": market_return, "color": "blue"},
        "Risk-Free Asset": {"beta": 0.0, "actual": risk_free_rate, "color": "green"},
    }

    # User-defined assets
    show_custom_assets = st.checkbox("Add custom assets", value=True)

if show_custom_assets:
    st.markdown("**Custom Assets**")
    col1, col2, col3 = st.columns(3)

    with col1:
        asset_a_beta = st.slider(
            "Asset A Beta",
            min_value=-0.5,
            max_value=2.5,
            value=1.3,
            step=0.1,
            key="beta_a",
        )
        asset_a_actual = st.slider(
            "Asset A Actual Return (%)",
            min_value=-5.0,
            max_value=25.0,
            value=14.0,
            step=0.5,
            key="actual_a",
        )

    with col2:
        asset_b_beta = st.slider(
            "Asset B Beta",
            min_value=-0.5,
            max_value=2.5,
            value=0.7,
            step=0.1,
            key="beta_b",
        )
        asset_b_actual = st.slider(
            "Asset B Actual Return (%)",
            min_value=-5.0,
            max_value=25.0,
            value=6.0,
            step=0.5,
            key="actual_b",
        )

    with col3:
        asset_c_beta = st.slider(
            "Asset C Beta",
            min_value=-0.5,
            max_value=2.5,
            value=1.8,
            step=0.1,
            key="beta_c",
        )
        asset_c_actual = st.slider(
            "Asset C Actual Return (%)",
            min_value=-5.0,
            max_value=25.0,
            value=12.0,
            step=0.5,
            key="actual_c",
        )

    assets["Asset A"] = {"beta": asset_a_beta, "actual": asset_a_actual, "color": "red"}
    assets["Asset B"] = {
        "beta": asset_b_beta,
        "actual": asset_b_actual,
        "color": "purple",
    }
    assets["Asset C"] = {
        "beta": asset_c_beta,
        "actual": asset_c_actual,
        "color": "orange",
    }

# Calculate market risk premium
market_risk_premium = market_return - risk_free_rate

# Generate SML line
betas = np.linspace(-0.5, 2.5, 100)
expected_returns = risk_free_rate + betas * market_risk_premium

# Create visualisation
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the SML
ax.plot(
    betas,
    expected_returns,
    "b-",
    linewidth=2,
    label="Security Market Line (SML)",
)

# Plot assets
for name, asset in assets.items():
    beta = asset["beta"]
    actual = asset["actual"]
    expected = risk_free_rate + beta * market_risk_premium
    alpha = actual - expected

    # Plot actual position
    marker = "o" if name in ["Market Portfolio", "Risk-Free Asset"] else "s"
    size = 150 if name in ["Market Portfolio", "Risk-Free Asset"] else 120
    ax.scatter(
        [beta],
        [actual],
        color=asset["color"],
        s=size,
        zorder=5,
        marker=marker,
        label=f"{name} (β={beta:.1f})",
    )

    # Draw vertical line to SML if there's alpha
    if abs(alpha) > 0.1 and name not in ["Market Portfolio", "Risk-Free Asset"]:
        ax.plot(
            [beta, beta],
            [actual, expected],
            color=asset["color"],
            linestyle="--",
            alpha=0.5,
            linewidth=1.5,
        )

# Add labels
ax.set_xlabel("Beta (Systematic Risk)", fontsize=12)
ax.set_ylabel("Expected Return (%)", fontsize=12)
ax.set_title("Security Market Line (SML)", fontsize=14)
ax.axhline(
    y=risk_free_rate,
    color="gray",
    linestyle=":",
    alpha=0.5,
    label=f"Risk-Free Rate = {risk_free_rate}%",
)
ax.axvline(x=0, color="gray", linestyle="-", alpha=0.3)
ax.axvline(x=1, color="gray", linestyle=":", alpha=0.5)
ax.legend(loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)

# Set axis limits
ax.set_xlim(-0.6, 2.6)
y_min = min(risk_free_rate - 2, min(expected_returns) - 2)
y_max = max(expected_returns) + 3
ax.set_ylim(y_min, y_max)

plt.tight_layout()
st.pyplot(fig)


st.markdown("#### Asset Analysis: Alpha (Jensen's Alpha)")

st.write(
    "**Alpha** measures the excess return of an asset compared to its CAPM-predicted return. "
    "It indicates whether an asset is overperforming or underperforming relative to its risk."
)

with st.expander(label="Alpha Formula", expanded=False):
    latex_alpha = r"""
        \alpha_i = R_i - E(R_i) = R_i - [R_f + \beta_i (R_m - R_f)] \\ \\

        where: \\
        \alpha_i = \text{Jensen's alpha for asset } i \\
        R_i = \text{actual return of asset } i \\
        E(R_i) = \text{CAPM expected return}
        """
    st.code(latex_alpha, language="latex")
    st.latex(latex_alpha)

if show_custom_assets:
    st.markdown("**Alpha Analysis for Custom Assets**")

    cols = st.columns(3)
    custom_assets = ["Asset A", "Asset B", "Asset C"]

    for i, name in enumerate(custom_assets):
        asset = assets[name]
        beta = asset["beta"]
        actual = asset["actual"]
        expected = risk_free_rate + beta * market_risk_premium
        alpha = actual - expected

        with cols[i]:
            st.markdown(f"**{name}**")
            st.metric("Beta", f"{beta:.2f}")
            st.metric("CAPM Expected Return", f"{expected:.2f}%")
            st.metric("Actual Return", f"{actual:.2f}%")

            if alpha > 0.1:
                st.success(f"Alpha: +{alpha:.2f}% (Undervalued)")
            elif alpha < -0.1:
                st.error(f"Alpha: {alpha:.2f}% (Overvalued)")
            else:
                st.info(f"Alpha: {alpha:.2f}% (Fairly Valued)")

st.write("""
**Interpreting Alpha:**
- **α > 0 (Above SML)**: Asset is undervalued — it delivers more return than CAPM predicts for its risk level. Buy signal.
- **α < 0 (Below SML)**: Asset is overvalued — it delivers less return than CAPM predicts for its risk level. Sell signal.
- **α = 0 (On SML)**: Asset is fairly valued according to CAPM.
""")


st.markdown("#### CAPM Assumptions and Limitations")

with st.expander("Key Assumptions", expanded=False):
    st.write("""
**CAPM relies on several simplifying assumptions:**

1. **Investors are rational and risk-averse** — they seek to maximise expected utility
2. **Markets are efficient** — all information is reflected in prices
3. **No transaction costs or taxes** — trading is frictionless
4. **Investors can borrow and lend at the risk-free rate** — unlimited leverage available
5. **Single-period investment horizon** — all investors have the same time frame
6. **Homogeneous expectations** — all investors agree on expected returns and risks
7. **Assets are infinitely divisible** — any fraction can be purchased
""")

with st.expander("Limitations and Critiques", expanded=False):
    st.write("""
**Real-world challenges with CAPM:**

1. **Beta instability** — beta changes over time and depends on the estimation period
2. **Single factor model** — ignores other risk factors (size, value, momentum)
3. **Market portfolio is unobservable** — we use proxies like S&P 500
4. **Empirical anomalies** — low-beta stocks often outperform CAPM predictions
5. **Risk-free rate assumption** — no truly risk-free asset exists
6. **Static model** — doesn't account for changing market conditions

**Extensions like the Fama-French 3-factor and 5-factor models address some limitations
by adding size and value factors.**
""")


st.markdown("#### Key Insights")

st.write("""
**Understanding the Security Market Line:**
- The SML shows the required return for any level of systematic risk (beta)
- The slope of the SML is the market risk premium: $E(R_m) - R_f$
- Steeper SML = higher reward for taking systematic risk
- All efficient portfolios should lie on the SML

**Practical Applications:**
- **Cost of equity estimation**: Companies use CAPM to determine required returns for projects
- **Portfolio evaluation**: Alpha measures manager skill (or luck) in beating risk-adjusted benchmarks
- **Asset allocation**: Understanding beta helps construct portfolios with desired risk profiles
- **Security selection**: Identify potentially mispriced securities above/below the SML
""")
