import streamlit as st


st.set_page_config(layout="wide")
st.markdown("### The Greeks")


st.markdown("#### Delta")

st.write(
    "The delta of an option, is the ratio of the change in the price of the call option, c, to the change in the price of the underlying asset, s, for small changes in s."
)

latex_code = r"""
    delta = \Delta = \frac{\delta c}{\delta s} \\ \\

    where: \\
    \delta c = \text change~in~the~call~price \\
    \delta s = \text change~in~the~underlying~asset~price \\
    """
st.code(latex_code, language="latex")
st.latex(latex_code)


st.markdown("#### Option Delta")

st.write(
    """A call delta equal to 0.7 means that the price of a call option on a stock will change by approximately £0.70 for a £1.00 change in the value of the stock.  To completely hedge a long stock or short call position, an investor must purchase the number of shares of stock equal to delta times the number of options sold."""
)

st.write("**Delta-neutral** means that the position is completely hedged.")

st.write(
    """E.g., if an investor is short 1,000 call options, they will need to be long 700 ($0.7 \cdot 1000$) shares of the underlying."""
)


st.markdown("#### Theta")

st.write(
    "Theta, $\Theta$, is the option's sensitivity to a decrease in time to expiration.  It is also known as 'time decay' and is a function of both time and the price of the underlying asset."
)


st.markdown("#### Gamma")

st.write(
    "Gamma, $\Gamma$, is the rate of change of delta of an option.  It measures the curvature of the option price function that is not captured by delta.  It is the second derivative of the option price with respect to the underlying asset price."
)
st.write("Gamma is always positive for long options and negative for short options.")
st.write(
    "Gamma is highest for at-the-money options and decreases as the option moves further in or out of the money."
)
latex_code = r"""
    gamma = \Gamma = \frac{\delta^2 c}{\delta s^2} \\ \\

    where: \\
    \delta^2 c = \text change~in~the~call~price \\
    \delta s^2 = \text change~in~the~underlying~asset~price \\
    """
st.code(latex_code, language="latex")
st.latex(latex_code)

st.write("**Delta-neutral** positions can hedge the portfolio against small changes in the underlying asset price.")
st.write(
    "**Gamma-neutral** positions can hedge the portfolio against large changes in the underlying asset price."
)


st.markdown("#### Vega")

st.write("Vega measures the sensitivity of the option's price to changes in the volatility of the underlying asset.")
st.write("A Vega of 7 means that a 1% increase in volatility will increase the price of the option by 0.07.")
st.write("For a given maturity, exercise price and risk-free rate, the Vega of a call option is equal to the Vega of a put option.")
st.write(
    "Vega is positive for long options and negative for short options as it increases the value of both option types.  " \
    "Vega is highest for at-the-money options and decreases as the option moves further in or out of the money."
)


st.markdown("#### Rho")
