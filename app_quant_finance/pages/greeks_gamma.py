import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from quant_finance.pricing.black_scholes import black_scholes_gamma

st.set_page_config(page_title="The Greeks - Gamma", page_icon="📊", layout="wide")
st.header("The Greeks - Gamma")


st.markdown("#### Gamma")

st.write(
    r"Gamma, $\Gamma$, is the rate of change of an option's delta with respect to the price of the underlying "
    "asset. It is the second partial derivative of the option price with respect to the underlying price, so it "
    "measures the curvature of the option price that delta does not capture."
)
st.write(
    "Gamma is positive for long calls and puts and negative for short ones, and a call and a put with the same "
    "strike and expiry have the same gamma."
)
st.write(
    "Gamma is highest for at-the-money options and falls as the option moves further in or out of the money. "
    "As expiry approaches, the gamma of an at-the-money option rises sharply."
)
st.write(
    "It can be thought of as a measure of how often a position needs to be rebalanced to stay delta-neutral: "
    "the larger the gamma, the faster delta drifts when the stock moves."
)

with st.expander(label="Gamma", expanded=True):
    latex_code = r"""
        \Gamma = \frac{\partial \Delta}{\partial S} = \frac{\partial^2 V}{\partial S^2} \\ \\
        \text{where:} \\
        V = \text{option price} \\
        S = \text{price of the underlying asset} \\
        \Delta = \text{delta of the option}
        """
    st.code(latex_code, language="latex")
    st.latex(latex_code)

with st.expander(label="Black-Scholes Gamma", expanded=False):
    latex_bs = r"""
        \Gamma = \frac{e^{-qT} N'(d_1)}{S \sigma \sqrt{T}} \\ \\
        N'(x) = \frac{1}{\sqrt{2\pi}} e^{-x^2 / 2}
        """
    st.code(latex_bs, language="latex")
    st.latex(latex_bs)


st.markdown("#### Interactive Example")

col1, col2, col3 = st.columns(3)
with col1:
    strike = st.number_input("Strike Price (K)", min_value=1.0, value=100.0, step=1.0)
    spot = st.number_input(
        "Current Stock Price (S)", min_value=1.0, value=100.0, step=1.0
    )
with col2:
    expiry = st.slider("Time to Expiry (years)", 0.05, 3.0, 1.0, 0.05)
    sigma = st.slider("Volatility (σ, %)", 1, 100, 20) / 100
with col3:
    rate = st.slider("Risk-free Rate (r, %)", 0.0, 10.0, 5.0, 0.25) / 100
    dividend = st.slider("Dividend Yield (q, %)", 0.0, 10.0, 0.0, 0.25) / 100

spots = np.linspace(0.5 * strike, 1.5 * strike, 300)

fig, ax = plt.subplots(figsize=(10, 5))
for fraction in (1.0, 0.25, 1 / 12):
    time = expiry * fraction
    ax.plot(
        spots,
        black_scholes_gamma(spots, strike, time, rate, sigma, dividend),
        label=f"T = {time:.2f} years",
    )
ax.axvline(spot, color="grey", linestyle="--", linewidth=1, label=f"S = {spot:.0f}")
ax.set_xlabel("Stock Price (S)")
ax.set_ylabel("Gamma")
ax.set_title("Black-Scholes Gamma against the Stock Price")
ax.legend()
ax.grid(True, alpha=0.3)

chart_col, metric_col = st.columns([3, 1])
with chart_col:
    st.pyplot(fig)
    plt.close(fig)
with metric_col:
    gamma = black_scholes_gamma(spot, strike, expiry, rate, sigma, dividend)
    st.metric("Gamma (call or put)", f"{gamma:.5f}")
    st.caption(f"A £1 rise in the stock changes delta by about {gamma:.4f}.")

st.write(
    "The curves show gamma concentrating around the strike as expiry approaches: a short-dated at-the-money "
    "option's delta can swing from near 0 to near 1 over a small move in the stock."
)


st.markdown("#### Gamma Hedging")

st.write(
    "**Delta-neutral** positions are hedged against small changes in the underlying asset price."
)
st.write(
    "**Gamma-neutral** positions are also hedged against larger changes, because delta then stays close to "
    "zero as the stock moves. The stock itself has zero gamma, so gamma can only be changed by trading "
    "options. A gamma hedge therefore has two steps:"
)
st.write(
    "1. Buy or sell options until the gamma of the whole position is zero.\n"
    "2. Those options change the position's delta, so buy or sell the stock to bring delta back to zero."
)

st.caption(
    "Hull, J.C. (2022). 'Options, Futures, and Other Derivatives', 11th ed. Pearson."
)
