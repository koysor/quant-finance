import streamlit as st

st.set_page_config(page_title="Fixed Income Toolkit", page_icon="🏦", layout="wide")

st.sidebar.title("🏦 Fixed Income")

st.header("Fixed Income Toolkit")

st.write(
    "Interactive pages on fixed income markets, built on live US Treasury data from "
    "FRED. Choose a page from the sidebar:"
)

st.markdown(
    "- **Treasury Yield Curve:** today's par yield curve from 1 month to 30 years, how "
    "it compares with earlier dates, what its shape says about expected interest "
    "rates, and the 10Y–2Y and 10Y–3M spreads over time."
)
