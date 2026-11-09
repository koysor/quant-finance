import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from quant_finance.pricing.black_scholes import black_scholes_vega

st.set_page_config(page_title="The Greeks - Vega", page_icon="📊", layout="wide")
st.header("The Greeks - Vega")


st.markdown("#### Vega")

st.write(
    "Vega measures the sensitivity of an option's price to changes in the volatility of the underlying asset. "
    "It is the partial derivative of the option price with respect to volatility."
)
st.write(
    "Vega is quoted in two ways, so always check the convention. Per unit of volatility it is the change in "
    "price if volatility rose by 1.00 (100 vol points); per vol point it is that figure divided by 100. For "
    "example, a vega of 7 per unit of volatility is 0.07 per vol point: a rise in volatility from 20% to 21% "
    "increases the option price by about 0.07."
)
st.write(
    "For a given underlying price, strike, expiry and risk-free rate, the vega of a European call equals the "
    "vega of a European put."
)
st.write(
    "Higher volatility increases the value of both calls and puts, so vega is positive for long options and "
    "negative for short options. Vega is highest for at-the-money options, falls as the option moves further "
    "in or out of the money, and rises with the time to expiry."
)

with st.expander(label="Vega", expanded=True):
    latex_code = r"""
        \mathcal{V} = \frac{\partial V}{\partial \sigma} \\ \\
        \text{where:} \\
        V = \text{option price} \\
        \sigma = \text{volatility of the underlying asset}
        """
    st.code(latex_code, language="latex")
    st.latex(latex_code)

with st.expander(label="Black-Scholes Vega", expanded=False):
    latex_bs = r"""
        \mathcal{V} = S e^{-qT} N'(d_1) \sqrt{T} \\ \\
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
        black_scholes_vega(spots, strike, time, rate, sigma, dividend) / 100,
        label=f"T = {time:.2f} years",
    )
ax.axvline(spot, color="grey", linestyle="--", linewidth=1, label=f"S = {spot:.0f}")
ax.set_xlabel("Stock Price (S)")
ax.set_ylabel("Vega per vol point")
ax.set_title("Black-Scholes Vega against the Stock Price")
ax.legend()
ax.grid(True, alpha=0.3)

chart_col, metric_col = st.columns([3, 1])
with chart_col:
    st.pyplot(fig)
    plt.close(fig)
with metric_col:
    vega = black_scholes_vega(spot, strike, expiry, rate, sigma, dividend)
    st.metric("Vega per unit of volatility", f"{vega:.3f}")
    st.metric("Vega per vol point", f"{vega / 100:.4f}")
    st.caption(
        f"A rise in volatility from {sigma:.0%} to {sigma + 0.01:.0%} increases the call "
        f"or put price by about £{vega / 100:.3f}."
    )

st.write(
    "Longer-dated options have more vega: there is more time for volatility to affect where the stock ends up."
)

st.caption(
    "Hull, J.C. (2022). 'Options, Futures, and Other Derivatives', 11th ed. Pearson."
)
