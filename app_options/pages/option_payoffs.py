import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Option Payoffs", page_icon="📈", layout="wide")
st.header("Option Payoffs")

option_position_type = st.selectbox(
    "Select Option Position Type",
    ["Long Call", "Short Call", "Long Put", "Short Put"],
    index=0,
    help="Select the type of option position to visualise the payoff.",
)


strike_price = st.number_input(
    "Strike Price",
    min_value=0.0,
    value=100.0,
    step=1.0,
    help="Enter the strike price of the option.",
)

premium = st.number_input(
    "Option Premium",
    min_value=0.0,
    value=10.0,
    step=0.5,
    help="Enter the premium paid/received for the option.",
)

# Generate stock price range for the payoff diagram
price_range = strike_price * 0.5
stock_prices = np.linspace(
    max(0, strike_price - price_range), strike_price + price_range, 200
)

# Calculate payoff based on position type
if option_position_type == "Long Call":
    payoff = np.maximum(stock_prices - strike_price, 0) - premium
    break_even = strike_price + premium
elif option_position_type == "Short Call":
    payoff = premium - np.maximum(stock_prices - strike_price, 0)
    break_even = strike_price + premium
elif option_position_type == "Long Put":
    payoff = np.maximum(strike_price - stock_prices, 0) - premium
    break_even = strike_price - premium
else:  # Short Put
    payoff = premium - np.maximum(strike_price - stock_prices, 0)
    break_even = strike_price - premium

# Create the matplotlib figure
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the payoff line
ax.plot(stock_prices, payoff, "b-", linewidth=2, label="Profit/Loss")

# Add zero line
ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

# Add strike price vertical line
ax.axvline(
    x=strike_price,
    color="red",
    linestyle="--",
    linewidth=1,
    label=f"Strike: £{strike_price:.2f}",
)

# Add break-even vertical line
if break_even > 0:
    ax.axvline(
        x=break_even,
        color="green",
        linestyle="--",
        linewidth=1,
        label=f"Break-even: £{break_even:.2f}",
    )

# Fill profit/loss regions
ax.fill_between(
    stock_prices,
    payoff,
    0,
    where=(payoff > 0),
    alpha=0.3,
    color="green",
    label="Profit",
)
ax.fill_between(
    stock_prices, payoff, 0, where=(payoff < 0), alpha=0.3, color="red", label="Loss"
)

# Labels and title
ax.set_xlabel("Stock Price at Expiration (£)", fontsize=12)
ax.set_ylabel("Profit/Loss (£)", fontsize=12)
ax.set_title(f"{option_position_type} Payoff Diagram", fontsize=14, fontweight="bold")
ax.legend(loc="best")
ax.grid(True, alpha=0.3)

# Create two columns: chart on left, text on right
col_chart, col_text = st.columns([3, 2])

with col_chart:
    st.pyplot(fig)

with col_text:
    st.markdown("#### Payoff Formulas")

    if option_position_type == "Long Call":
        st.latex(r"\text{Payoff} = \max(S_T - K, 0) - \text{Premium}")
        st.markdown("**Max Loss:** Premium paid (limited)")
        st.markdown("**Max Profit:** Unlimited")
    elif option_position_type == "Short Call":
        st.latex(r"\text{Payoff} = \text{Premium} - \max(S_T - K, 0)")
        st.markdown("**Max Loss:** Unlimited")
        st.markdown("**Max Profit:** Premium received (limited)")
    elif option_position_type == "Long Put":
        st.latex(r"\text{Payoff} = \max(K - S_T, 0) - \text{Premium}")
        st.markdown("**Max Loss:** Premium paid (limited)")
        st.markdown(
            f"**Max Profit:** £{strike_price - premium:.2f} (if stock goes to £0)"
        )
    else:  # Short Put
        st.latex(r"\text{Payoff} = \text{Premium} - \max(K - S_T, 0)")
        st.markdown(
            f"**Max Loss:** £{strike_price - premium:.2f} (if stock goes to £0)"
        )
        st.markdown("**Max Profit:** Premium received (limited)")

    st.markdown(f"""
Where:
- $S_T$ = Stock price at expiration
- $K$ = Strike price (£{strike_price:.2f})
- Premium = £{premium:.2f}
- Break-even = £{break_even:.2f}
""")
