import streamlit as st

st.set_page_config(
    page_title="Quantitative Finance Toolkit", page_icon="📊", layout="wide"
)

st.sidebar.title("📊 Quantitative Finance")
st.sidebar.info(
    "Explore stochastic processes, option Greeks, volatility modelling, "
    "and risk management through interactive visualisations and worked examples."
)

st.header("Quantitative Finance Toolkit")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.image("app_quant_finance/assets/quantitative_finance.png")
