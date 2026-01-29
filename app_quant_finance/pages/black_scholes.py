import streamlit as st

st.set_page_config(layout="wide")
st.markdown("### Black-Scholes Model")


st.write(
    "The Black-Scholes model can be used to calculate the theoretical price of European call and put options."
)
st.write(
    "The model assumes that the stock price follows a geometric Brownian motion with constant volatility and interest rate."
    "The Black-Scholes equation is a **partial differential equation** (PDE) that governs the price evolution of "
    "financial derivatives, such as options."
    "It models the price $V(t,S)$ of an option as a function of the underlying asset price $S$ and time $t$."
)

st.write(
    "It can help us determine the fair price of an option using mathematics that predicts how stock prices could change over time.  "
)


st.markdown("#### The Black-Scholes Partial Differential Equation (PDE)")

latex_code = r"""
\frac{\partial V}{\partial t} + \frac{1}{2} \sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + r S \frac{\partial V}{\partial S} - r V = 0"""
st.code(latex_code, language="latex")
st.latex(latex_code)

st.write("Where:")
st.write("- $V(t,S)$ is the option price as a function of time $t$ and stock price $S$")
st.write("- $\sigma$ is the volatility of the underlying stock")
st.write("- $r$ is the risk-free interest rate")
st.write(
    r"- $\frac{\partial V}{\partial t}$ is the partial derivative of $V$ with respect to time"
)
st.write(
    r"- $\frac{\partial V}{\partial S}$ is the partial derivative of $V$ with respect to stock price"
)
st.write(
    r"- $\frac{\partial^2 V}{\partial S^2}$ is the second partial derivative of $V$ with respect to stock price"
)


st.write("Explanation of the terms:")

st.latex(r"\frac{\partial V}{\partial t}")
st.write(
    "The **rate of change of the option price with respect to time** (time decay).  "
    "How the option's value changes (decreases) as time moves closer to expiration."
)

st.latex(r"\frac{1}{2} \sigma^2 S^2 \frac{\partial^2 V}{\partial S^2}")
st.write(
    "The effect of **volatility** and **curvature** (convexity) of the option price with respect "
    "to stock price changes.  This term accounts for how the option price reacts to the uncertainty of stock price movements"
    " capturing the risk related to price fluctuations."
)

st.latex(r"r S \frac{\partial V}{\partial S} ")
st.write(
    "The **expected growth rate of the option price from the underlying stock's price increase** "
    "at the risk-free interest rate.  This reflects the option price's sensitivity (delta) to changes in the stock "
    "price, scaled by the interest rate."
)

st.latex(r"- r V")
st.write(
    "The **cost of carrying or financing the option's price**, discounted at the risk-free rate. "
    "This term accounts for the fact that money tied up in the option could have earned interest elsewhere."
)

st.write(
    "The four terms sum to zero in the Black-Scholes equation, reflecting a fair, no-arbitrage price "
    "for the option given the underlying assumptions."
)
