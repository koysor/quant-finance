import streamlit as st


st.set_page_config(layout="wide")
st.markdown("### Wiener Process")


st.write(
    "A **Wiener process**, also known as **Brownian motion**, is a continuous-time stochastic process that is widely used in finance to model random movements in asset prices."
)
st.write("A Wiener process $$W(t)$$ has the following properties:")
st.write("$$t$$ represents the time variable")
st.write(
    "With **independent increments**, the movement between $$W(t)$$ and $$W(s)$$ is independent of the past."
)
latex_code = r"""
W(t) - W(s) \sim N(0, t - s)
"""
st.code(latex_code, language="latex")
st.latex(latex_code)

st.write("$$W(t)$$ is the value of the Wiener process at time $$t$$.")
st.write("$$W(s)$$ is the value of the Wiener process at time $$s$$.")
st.write(
    "**Normally distributed increments**: The increment $$W(s) - W(t)$$ is normally distributed with **mean 0** and **variance $$t - s$$**."
)


st.markdown("##### Asset Pricing with a Wiener Process")
st.write("Asset prices can be modelled as a **stochastic process**.")

latex_code = r"""
dS(t) = \mu S(t) dt + \sigma S(t) dW(t)
"""
st.code(latex_code, language="latex")
st.latex(latex_code)
st.write("Where:")
st.write("$$S(t)$$ is the asset price at time $$t$$.")
st.write("$$dt$$ is the time-step, the infinitesimal time increment.")
st.write("$$\mu$$ is the drift term, representing the expected return of the asset.")
st.write(
    "$$\sigma$$ is the volatility of the asset, representing the standard deviation of the asset's returns."
)
st.write(
    "$$dW(t)$$ is the increment of the Wiener process, representing the random shock to the asset price."
)
