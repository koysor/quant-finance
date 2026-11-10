import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from quant_finance.rates.treasury import (
    TENOR_YEARS,
    curve_on,
    fetch_treasury_par_yields,
    yield_spread,
)

st.set_page_config(page_title="Treasury Yield Curve", page_icon="🏦", layout="wide")
st.header("US Treasury Yield Curve")

st.write(
    "The yield curve plots the yield of government bonds against their maturity. The US "
    "Treasury curve is the reference curve for US dollar rates: it is the benchmark that "
    "corporate bonds, mortgages and swaps are priced against, and its shape summarises "
    "what the market expects for interest rates, inflation and growth."
)

st.info(
    "The yields on this page are the Federal Reserve's constant-maturity Treasury (CMT) "
    "yields from FRED. Each is the **par yield** of a notional Treasury with exactly that "
    "maturity: the coupon rate at which it would trade at par. The US Treasury "
    "interpolates them from the closing prices of the most recently auctioned "
    "securities. Every tenor, bills included, is quoted on the same bond-equivalent "
    "basis, in percent a year, so the tenors can be compared directly."
)


@st.cache_data(ttl=6 * 3600, show_spinner="Downloading yields from FRED...")
def load_yields(
    maturities: tuple[str, ...] | None, start: dt.date, end: dt.date
) -> pd.DataFrame:
    return fetch_treasury_par_yields(
        list(maturities) if maturities else None, start, end
    )


today = dt.date.today()

st.markdown("#### The curve on a date")

col1, col2 = st.columns(2)
with col1:
    curve_date = st.date_input(
        "Curve date",
        value=today,
        min_value=dt.date(1990, 1, 2),
        max_value=today,
        help="On a weekend or holiday, the previous business day's curve is shown",
    )
with col2:
    comparisons = st.multiselect(
        "Compare with the curve",
        options=["1 month earlier", "1 year earlier", "5 years earlier"],
        default=["1 year earlier"],
    )

offsets = {
    "1 month earlier": pd.DateOffset(months=1),
    "1 year earlier": pd.DateOffset(years=1),
    "5 years earlier": pd.DateOffset(years=5),
}
earliest = min(
    (pd.Timestamp(curve_date) - offsets[c] for c in comparisons),
    default=pd.Timestamp(curve_date),
)
# Ten extra days so a comparison date on a holiday weekend still finds a curve
start = (earliest - pd.Timedelta(days=10)).date()

try:
    yields = load_yields(None, start, curve_date)
    curve = curve_on(yields, curve_date)
except Exception as error:  # noqa: BLE001 - shown to the user instead
    st.error(f"Could not load Treasury yields from FRED: {error}")
    st.stop()

curves = {f"{curve.name:%d %b %Y}": curve}
for label in comparisons:
    on = pd.Timestamp(curve_date) - offsets[label]
    try:
        earlier = curve_on(yields, on)
    except ValueError:
        st.warning(f"No yields on or before {on:%d %b %Y}")
        continue
    curves[f"{earlier.name:%d %b %Y} ({label})"] = earlier

fig, ax = plt.subplots(figsize=(10, 5))
for i, (label, values) in enumerate(curves.items()):
    years = [TENOR_YEARS[tenor] for tenor in values.index]
    ax.plot(
        years,
        values.values,
        marker="o",
        linewidth=2.5 if i == 0 else 1.5,
        alpha=1.0 if i == 0 else 0.7,
        label=label,
    )
# A square-root scale spreads out the short end, where most tenors are
ax.set_xscale("function", functions=(np.sqrt, np.square))
ax.set_xticks(list(TENOR_YEARS.values()))
ax.set_xticklabels(list(TENOR_YEARS), fontsize=8)
ax.set_xlabel("Maturity (square-root scale)")
ax.set_ylabel("Par yield (% a year)")
ax.set_title("US Treasury par yield curve")
ax.grid(True, alpha=0.3)
ax.legend()
st.pyplot(fig)
plt.close(fig)

table = pd.DataFrame({label: values for label, values in curves.items()}).reindex(
    [tenor for tenor in TENOR_YEARS if tenor in curve.index]
)
if len(curves) > 1:
    first = next(iter(curves))
    for label in list(curves)[1:]:
        table[f"Change since {label.split(' (')[0]} (bp)"] = (
            (table[first] - table[label]) * 100
        ).round(0)
st.dataframe(table.style.format("{:.2f}", subset=list(curves)), width="stretch")

if curve.index.isin(["2Y", "10Y"]).sum() == 2:
    slope = (curve["10Y"] - curve["2Y"]) * 100
    shape = "upward sloping" if slope > 25 else "inverted" if slope < -25 else "flat"
    st.write(
        f"On {curve.name:%d %B %Y} the 10-year yield was {slope:+.0f} basis points "
        f"above the 2-year yield, so between those tenors the curve was **{shape}**."
    )

st.markdown("#### Reading the shape of the curve")

st.write(
    "- **Upward sloping (normal):** longer maturities yield more. Investors expect "
    "short rates to stay level or rise, and ask for a premium for tying money up "
    "for longer.\n"
    "- **Flat:** yields are similar across maturities, often in the transition "
    "between the other two shapes.\n"
    "- **Inverted:** short maturities yield more than long ones. The market expects "
    "the central bank to cut rates in future, usually because it expects growth or "
    "inflation to fall.\n"
    "- **Humped:** the middle of the curve yields more than both ends, for example "
    "when hikes are expected in the near term and cuts later."
)

with st.expander(label="Expectations hypothesis and the term premium", expanded=True):
    st.write(
        "Under the **expectations hypothesis**, an investor should be indifferent "
        "between buying an n-year bond and rolling over one-year bonds for n years. "
        "So the n-year yield is the average of the expected future one-year rates. In "
        "practice investors also ask for a **term premium** for bearing the risk of "
        "holding long bonds, whose prices move more when rates change:"
    )
    st.latex(
        r"""
        y_n \approx \frac{1}{n} \sum_{i=0}^{n-1} \mathbb{E}_t\left[r_{t+i}\right]
        + TP_n \\ \\
        \text{where: } y_n = n\text{-year yield}, \quad
        r_{t+i} = \text{one-year rate in year } t+i, \quad
        TP_n = \text{term premium}
        """
    )
    st.write(
        "The slope of the curve therefore mixes two things that cannot be observed "
        "separately: the expected path of short rates and the term premium. A positive "
        "term premium is why the curve slopes upward when rates are expected to stay "
        "where they are."
    )

st.markdown("#### Curve spreads over time")

st.write(
    'Two spreads summarise the slope of the curve: **10Y–2Y** ("2s10s"), widely '
    "quoted by traders, and **10Y–3M**, which the Federal Reserve Bank of New York "
    "uses in its recession probability model. A negative spread means that segment of "
    "the curve is inverted."
)

history_years = st.slider("Years of history", min_value=2, max_value=30, value=10)
history_start = (pd.Timestamp(today) - pd.DateOffset(years=history_years)).date()

try:
    history = load_yields(("3M", "2Y", "10Y"), history_start, today)
except Exception as error:  # noqa: BLE001 - shown to the user instead
    st.error(f"Could not load Treasury yields from FRED: {error}")
    st.stop()

spreads = pd.concat(
    [
        yield_spread(history, long="10Y", short="2Y"),
        yield_spread(history, long="10Y", short="3M"),
    ],
    axis=1,
)

fig, ax = plt.subplots(figsize=(10, 4))
for column in spreads.columns:
    ax.plot(spreads.index, spreads[column] * 100, linewidth=1, label=column)
inverted = spreads["10Y-3M"] < 0
ax.fill_between(
    spreads.index,
    0,
    1,
    where=inverted.to_numpy(),
    transform=ax.get_xaxis_transform(),
    color="red",
    alpha=0.1,
    label="10Y-3M inverted",
)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_ylabel("Spread (basis points)")
ax.set_title("US Treasury curve spreads")
ax.grid(True, alpha=0.3)
ax.legend(loc="upper left")
st.pyplot(fig)
plt.close(fig)

latest = spreads.dropna().iloc[-1]
c1, c2, c3 = st.columns(3)
c1.metric("10Y-2Y now", f"{latest['10Y-2Y'] * 100:+.0f} bp")
c2.metric("10Y-3M now", f"{latest['10Y-3M'] * 100:+.0f} bp")
c3.metric(
    "Days 10Y-3M inverted in the window",
    f"{int(inverted.sum()):,} of {len(spreads):,}",
)

st.warning(
    "An inverted 10Y–3M spread has preceded every US recession since the late 1960s, "
    "which is why it is watched so closely. It is a signal, not a law: the lag from "
    "inversion to recession has varied from a few months to about two years, and an "
    "inversion can also reflect a low term premium (for example from central bank bond "
    "buying) rather than expected rate cuts."
)

st.caption(
    "Source: Board of Governors of the Federal Reserve System, H.15 Selected Interest "
    "Rates, via FRED (series DGS1MO to DGS30). Yields are daily; the latest value is "
    "usually from the previous business day."
)
