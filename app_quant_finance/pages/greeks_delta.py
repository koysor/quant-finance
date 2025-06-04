import streamlit as st


st.set_page_config(layout="wide")
st.markdown("### The Greeks - Delta")


st.markdown("#### Delta")

st.write(
    "The delta of an option, is the ratio of the change in the price of the call option, c, to the change in the price of the underlying asset, s, for small changes in s.  I.e. the sensitivity of the option price to changes in the underlying stock price."
)

with st.expander(label="Delta", expanded=True):
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

st.write(
    "The delta changes as the stock  price and time change, therefore in order to maintain a **delta-neutral** position the number of assets held must be continually adjusted buy by buying and selling the stock.  This is known as **hedging** or **rebalancing** of the portfolio.  Also known as **dynamic hedging**. "
)