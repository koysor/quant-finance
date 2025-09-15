import streamlit as st


st.set_page_config(layout="wide")
st.markdown("### The Greeks - Theta")


st.markdown("#### Theta")

st.write(
    "Theta, $\Theta$, is the option's sensitivity to a decrease in time to expiration.  It is also known as 'time decay' and is a function of both time and the price of the underlying asset."
)

with st.expander(label="Theta", expanded=True):
    latex_code = r"""
        theta = \Theta = \frac{\delta c}{\delta t} \\ \\

        where: \\
        \delta c = \text change~in~the~call~price \\
        \delta t = \text change~in~time \\
        """
    st.code(latex_code, language="latex")
    st.latex(latex_code)

st.write("Theta is negative for long options and positive for short options.")
st.write(
    "Theta is highest for at-the-money options and decreases as the option moves further in or out of the money."
)
st.write(
    "Theta is related to value of the option, the delta and the gamma by the Black-Scholes formula."
)
