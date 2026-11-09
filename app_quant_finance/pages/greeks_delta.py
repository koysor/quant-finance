import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from quant_finance.pricing.black_scholes import black_scholes_delta

st.set_page_config(page_title="The Greeks - Delta", page_icon="📊", layout="wide")
st.header("The Greeks - Delta")


st.markdown("#### Delta")

st.write(
    "The delta of an option is the rate of change of the option price, V, with respect to the price of the "
    "underlying asset, S. It is the first partial derivative of the option price with respect to S: "
    "the sensitivity of the option price to small changes in the underlying stock price."
)

with st.expander(label="Delta", expanded=True):
    latex_code = r"""
        \Delta = \frac{\partial V}{\partial S} \\ \\
        \text{where:} \\
        V = \text{option price} \\
        S = \text{price of the underlying asset}
        """
    st.code(latex_code, language="latex")
    st.latex(latex_code)

with st.expander(label="Black-Scholes Delta", expanded=False):
    latex_bs = r"""
        \Delta_{\text{call}} = e^{-qT} N(d_1) \\ \\
        \Delta_{\text{put}} = -e^{-qT} N(-d_1) = \Delta_{\text{call}} - e^{-qT} \\ \\
        d_1 = \frac{\ln(S / K) + (r - q + \sigma^2 / 2) T}{\sigma \sqrt{T}}
        """
    st.code(latex_bs, language="latex")
    st.latex(latex_bs)
    st.write(
        "A call's delta lies between 0 and 1 and a put's between −1 and 0 (between 0 and "
        "$e^{-qT}$ in size when the stock pays a dividend yield $q$)."
    )


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
args = (strike, expiry, rate, sigma, dividend)
call_delta = black_scholes_delta(spot, *args, option_type="call")
put_delta = black_scholes_delta(spot, *args, option_type="put")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(spots, black_scholes_delta(spots, *args, option_type="call"), label="Call")
ax.plot(spots, black_scholes_delta(spots, *args, option_type="put"), label="Put")
ax.axvline(spot, color="grey", linestyle="--", linewidth=1, label=f"S = {spot:.0f}")
ax.axhline(0, color="black", linewidth=0.5)
ax.set_xlabel("Stock Price (S)")
ax.set_ylabel("Delta")
ax.set_title("Black-Scholes Delta against the Stock Price")
ax.legend()
ax.grid(True, alpha=0.3)

chart_col, metric_col = st.columns([3, 1])
with chart_col:
    st.pyplot(fig)
    plt.close(fig)
with metric_col:
    st.metric("Call Delta", f"{call_delta:.4f}")
    st.metric("Put Delta", f"{put_delta:.4f}")

st.write(
    "Delta moves towards 1 (call) or −1 (put) as the option moves into the money, and towards 0 "
    "as it moves out of the money. The shorter the time to expiry, the steeper the change around the strike."
)


st.markdown("#### Option Delta and Hedging")

st.write(
    f"With these inputs the call delta is {call_delta:.2f}, so the call price changes by approximately "
    f"£{call_delta:.2f} for a £1.00 change in the stock price. To hedge a short call position, an investor "
    "buys delta shares of stock for each option sold."
)

st.write(
    "**Delta-neutral** means that the position has no exposure to small moves in the stock."
)

st.write(
    f"E.g., if an investor is short 1,000 of these call options, they need to be long "
    f"{1000 * call_delta:,.0f} (${call_delta:.2f} \\cdot 1000$) shares of the underlying."
)

st.write(
    "The delta changes as the stock price and time change, so to keep a position **delta-neutral** the "
    "number of shares held must be adjusted continually by buying and selling the stock. This is known as "
    "**rebalancing** or **dynamic hedging**."
)

st.caption(
    "Hull, J.C. (2022). 'Options, Futures, and Other Derivatives', 11th ed. Pearson."
)
