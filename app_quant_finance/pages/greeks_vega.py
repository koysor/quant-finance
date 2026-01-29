import streamlit as st

st.set_page_config(layout="wide")
st.markdown("### The Greeks - Vega")


st.markdown("#### Vega")

st.write(
    "Vega measures the sensitivity of the option's price to changes in the volatility of the underlying asset."
)
st.write(
    "A Vega of 7 means that a 1% increase in volatility will increase the price of the option by 0.07."
)
st.write(
    "For a given maturity, exercise price and risk-free rate, the Vega of a call option is equal to the Vega of a put option."
)
st.write(
    "Vega is positive for long options and negative for short options as it increases the value of both option types.  "
    "Vega is highest for at-the-money options and decreases as the option moves further in or out of the money."
)
