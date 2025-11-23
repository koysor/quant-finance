import streamlit as st


st.set_page_config(layout="wide")

st.markdown(
    "### An application to demonstrate snippets of Python and LaTex code for Quantitative Finance"
)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.image("app_quant_finance/assets/quantitative_finance.png")
