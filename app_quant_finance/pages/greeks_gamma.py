import streamlit as st


st.set_page_config(layout="wide")
st.markdown("### The Greeks - Gamma")


st.markdown("#### Gamma")

st.write(
    r"Gamma, $$\Gamma$$, is the rate of change of delta of an option.  It measures the curvature of the option price function that is not captured by delta.  It is the second derivative of the option price with respect to the underlying asset price.  I.e. the sensitivity of the delta to the underlying stock price."
)
st.write("Gamma is always positive for long options and negative for short options.")
st.write(
    "Gamma is highest for at-the-money options and decreases as the option moves further in or out of the money."
)
st.write(
    "It can be thouht of as a measure of how often a position needs to be rebalanced in order to maintain a delta-neutral position ."
)

with st.expander(label="Gamma", expanded=True):
    latex_code = r"""
        gamma = \Gamma = \frac{\delta^2 c}{\delta s^2} \\ \\

        where: \\
        \delta^2 c = \text change~in~the~call~price \\
        \delta s^2 = \text change~in~the~underlying~asset~price \\
        """
    st.code(latex_code, language="latex")
    st.latex(latex_code)

st.write(
    "**Delta-neutral** positions can hedge the portfolio against small changes in the underlying asset price."
)
st.write(
    "**Gamma-neutral** positions can hedge the portfolio against large changes in the underlying asset price.  This can be done by buying or selling options to offset the delta of the portfolio.  This is known as **gamma hedging**."
)
