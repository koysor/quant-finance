import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import sys
    from pathlib import Path

    # Add project root to path for src imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return Path, mo, plt, sys


@app.cell
def _(mo):
    mo.md("""
    # Data Ingestion Examples

    This notebook demonstrates every data item and fetcher available in the
    `data_ingestion` package. Each section fetches a small sample of data and
    shows how it can be used in common quantitative finance workflows.

    **Data sources:** Yahoo Finance (via yfinance)

    **Fetchers covered:**
    1. `EquityFetcher` — historical OHLCV, batch fetch, real-time quotes, stock info
    2. `OptionsFetcher` — expirations, option chains, Greeks
    3. `FixedIncomeFetcher` — treasury yields, yield curves
    """)
    return


# ---------------------------------------------------------------------------
# Section 1: Equity Data
# ---------------------------------------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 1. Equity Data (`EquityFetcher`)
    """)
    return


@app.cell
def _():
    from src.data_ingestion import EquityFetcher, FetchError

    equity_fetcher = EquityFetcher()
    return EquityFetcher, FetchError, equity_fetcher


# --- 1.1 Historical OHLCV (single symbol) --------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 1.1 Historical OHLCV — Single Symbol

    Fetch daily Open, High, Low, Close, Volume data for Apple (AAPL).

    **Quant use cases:** VaR, backtesting, volatility modelling, Monte Carlo simulation.
    """)
    return


@app.cell
def _(equity_fetcher, mo):
    df_aapl = equity_fetcher.fetch_historical(
        symbol="AAPL",
        start_date="2024-11-01",
        end_date="2024-12-31",
        interval="1d",
    )

    mo.md(f"Fetched **{len(df_aapl)} rows** of daily AAPL data.")
    return (df_aapl,)


@app.cell
def _(df_aapl):
    df_aapl.head(10)
    return


@app.cell
def _(df_aapl, mo, plt):
    fig_aapl, ax_aapl = plt.subplots(figsize=(10, 4))
    ax_aapl.plot(df_aapl.index, df_aapl["Close"], linewidth=1.5)
    ax_aapl.set_title("AAPL Daily Close — Nov–Dec 2024", fontweight="bold")
    ax_aapl.set_ylabel("Price ($)")
    ax_aapl.grid(True, alpha=0.3)
    ax_aapl.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    mo.as_html(fig_aapl)
    return ax_aapl, fig_aapl


# --- 1.2 Historical OHLCV (batch fetch) ----------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 1.2 Historical OHLCV — Batch Fetch (Multiple Symbols)

    Fetch the same date range for several symbols in one call.

    **Quant use cases:** Portfolio optimisation (MPT), correlation analysis,
    cross-asset VaR, pairs trading, factor models.
    """)
    return


@app.cell
def _(equity_fetcher, mo):
    symbols = ["AAPL", "MSFT", "GOOGL"]
    multi_data = equity_fetcher.fetch_multiple(
        symbols=symbols,
        start_date="2024-11-01",
        end_date="2024-12-31",
    )

    for sym, df in multi_data.items():
        mo.output.append(mo.md(f"**{sym}**: {len(df)} rows"))
    return multi_data, symbols


@app.cell
def _(mo, multi_data, plt):
    fig_multi, ax_multi = plt.subplots(figsize=(10, 4))
    for sym, df in multi_data.items():
        # Normalise to 100 at start for comparison
        normalised = df["Close"] / df["Close"].iloc[0] * 100
        ax_multi.plot(normalised.index, normalised, label=sym, linewidth=1.5)
    ax_multi.set_title("Normalised Close Prices — Nov–Dec 2024", fontweight="bold")
    ax_multi.set_ylabel("Indexed (100 = start)")
    ax_multi.legend()
    ax_multi.grid(True, alpha=0.3)
    ax_multi.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    mo.as_html(fig_multi)
    return ax_multi, fig_multi


# --- 1.3 Real-time Quote -------------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 1.3 Real-Time Quote

    Fetch the latest price snapshot for a symbol.

    **Quant use cases:** Live portfolio valuation, intraday risk monitoring,
    execution benchmarking.
    """)
    return


@app.cell
def _(equity_fetcher, mo):
    quote = equity_fetcher.fetch_realtime_quote("AAPL")

    mo.md(f"""
    | Field | Value |
    |-------|-------|
    | **Symbol** | {quote["symbol"]} |
    | **Price** | ${quote["price"]:.2f} |
    | **Previous Close** | ${quote["previous_close"]:.2f} |
    | **Open** | ${quote["open"]:.2f} |
    | **Day High** | ${quote["day_high"]:.2f} |
    | **Day Low** | ${quote["day_low"]:.2f} |
    | **Volume** | {quote["volume"]:,} |
    | **Market Cap** | ${quote["market_cap"]:,.0f} |
    | **Currency** | {quote["currency"]} |
    """)
    return (quote,)


# --- 1.4 Stock Information / Fundamentals ---------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 1.4 Stock Information / Fundamentals

    Fetch company metadata, financials, and key ratios.

    **Quant use cases:** Factor models (Fama-French), fundamental screening,
    risk decomposition (beta), sector rotation, dividend discount models.
    """)
    return


@app.cell
def _(equity_fetcher, mo):
    info = equity_fetcher.get_info("AAPL")

    _fields = {
        "Company": info.get("longName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Market Cap": f"${info.get('marketCap', 0):,.0f}",
        "Trailing P/E": f"{info.get('trailingPE', 'N/A')}",
        "Forward P/E": f"{info.get('forwardPE', 'N/A')}",
        "Dividend Yield": (
            f"{info.get('dividendYield', 0):.2%}"
            if info.get("dividendYield")
            else "N/A"
        ),
        "Beta": f"{info.get('beta', 'N/A')}",
        "52-Week Change": (
            f"{info.get('52WeekChange', 0):.2%}" if info.get("52WeekChange") else "N/A"
        ),
        "Book Value": f"${info.get('bookValue', 'N/A')}",
        "Price-to-Book": f"{info.get('priceToBook', 'N/A')}",
        "Profit Margins": (
            f"{info.get('profitMargins', 0):.2%}"
            if info.get("profitMargins")
            else "N/A"
        ),
    }

    _rows = "\n".join(f"| **{k}** | {v} |" for k, v in _fields.items())
    mo.md(f"""
    | Field | Value |
    |-------|-------|
    {_rows}
    """)
    return (info,)


# ---------------------------------------------------------------------------
# Section 2: Options Data
# ---------------------------------------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 2. Options Data (`OptionsFetcher`)
    """)
    return


@app.cell
def _():
    from src.data_ingestion import OptionsFetcher

    options_fetcher = OptionsFetcher()
    return OptionsFetcher, options_fetcher


# --- 2.1 Available Expirations -------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 2.1 Available Expirations

    List all expiration dates for which options data is available.

    **Quant use cases:** Volatility term structure analysis, calendar spread /
    roll-over strategy planning.
    """)
    return


@app.cell
def _(mo, options_fetcher):
    expirations = options_fetcher.get_available_expirations("AAPL")

    mo.md(f"""
    **AAPL** has **{len(expirations)}** available option expirations.

    First 10: {", ".join(expirations[:10])}
    """)
    return (expirations,)


# --- 2.2 Options Chain (Calls & Puts) ------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 2.2 Options Chain — Calls & Puts

    Fetch the full chain for a specific expiration, returning separate
    DataFrames for calls and puts.

    **Quant use cases:** Implied volatility surface, options pricing
    (Black-Scholes), Greeks, put-call parity, volatility trading,
    hedging, liquidity analysis, risk-neutral density extraction.
    """)
    return


@app.cell
def _(expirations, mo, options_fetcher):
    # Use the nearest available expiration
    _exp = expirations[0]
    calls, puts = options_fetcher.fetch_option_chain("AAPL", _exp)

    mo.md(f"""
    Expiration **{_exp}**: **{len(calls)}** calls, **{len(puts)}** puts
    """)
    return calls, puts


@app.cell
def _(calls, mo):
    mo.md("**Call options (first 10 rows):**")
    return


@app.cell
def _(calls):
    calls[
        ["Strike", "Last", "Bid", "Ask", "Volume", "OpenInterest", "ImpliedVolatility"]
    ].head(10)
    return


@app.cell
def _(mo):
    mo.md("**Put options (first 10 rows):**")
    return


@app.cell
def _(puts):
    puts[
        ["Strike", "Last", "Bid", "Ask", "Volume", "OpenInterest", "ImpliedVolatility"]
    ].head(10)
    return


@app.cell
def _(calls, mo, plt, puts):
    fig_iv, ax_iv = plt.subplots(figsize=(10, 4))
    ax_iv.plot(
        calls["Strike"],
        calls["ImpliedVolatility"],
        label="Calls",
        marker="o",
        markersize=3,
    )
    ax_iv.plot(
        puts["Strike"],
        puts["ImpliedVolatility"],
        label="Puts",
        marker="s",
        markersize=3,
    )
    ax_iv.set_title("Implied Volatility Smile", fontweight="bold")
    ax_iv.set_xlabel("Strike ($)")
    ax_iv.set_ylabel("Implied Volatility")
    ax_iv.legend()
    ax_iv.grid(True, alpha=0.3)
    plt.tight_layout()
    mo.as_html(fig_iv)
    return ax_iv, fig_iv


# --- 2.3 Options with Greeks (by type) -----------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 2.3 Options by Type (with available Greeks)

    Fetch only calls or puts for a given expiration. yfinance provides
    implied volatility natively; full Greeks (delta, gamma, theta, vega)
    require a pricing model such as Black-Scholes.

    **Quant use cases:** Portfolio Greeks aggregation, dynamic hedging,
    risk limits monitoring.
    """)
    return


@app.cell
def _(expirations, options_fetcher):
    _exp = expirations[0]
    greeks_calls = options_fetcher.fetch_greeks("AAPL", _exp, option_type="call")
    greeks_calls[["Strike", "Last", "ImpliedVolatility"]].head(10)
    return (greeks_calls,)


# ---------------------------------------------------------------------------
# Section 3: Fixed Income Data
# ---------------------------------------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 3. Fixed Income Data (`FixedIncomeFetcher`)
    """)
    return


@app.cell
def _():
    from src.data_ingestion import FixedIncomeFetcher

    fi_fetcher = FixedIncomeFetcher()
    return FixedIncomeFetcher, fi_fetcher


# --- 3.1 Treasury Yields (time series) -----------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 3.1 Treasury Yields — Time Series

    Fetch historical yield data for selected maturities.

    **Quant use cases:** Risk-free rate (Black-Scholes, CAPM), bond pricing,
    duration and convexity, interest rate VaR, yield spread analysis (2s10s),
    discount curve construction, macro factor models.
    """)
    return


@app.cell
def _(fi_fetcher, mo):
    yields_df = fi_fetcher.fetch_treasury_yields(
        maturities=["3M", "5Y", "10Y", "30Y"],
        start_date="2024-10-01",
        end_date="2024-12-31",
    )

    mo.md(f"Fetched **{len(yields_df)} rows** of treasury yield data.")
    return (yields_df,)


@app.cell
def _(yields_df):
    yields_df.head(10)
    return


@app.cell
def _(mo, plt, yields_df):
    fig_yields, ax_yields = plt.subplots(figsize=(10, 4))
    for col in yields_df.columns:
        ax_yields.plot(yields_df.index, yields_df[col], label=col, linewidth=1.5)
    ax_yields.set_title("US Treasury Yields — Oct–Dec 2024", fontweight="bold")
    ax_yields.set_ylabel("Yield (%)")
    ax_yields.legend()
    ax_yields.grid(True, alpha=0.3)
    ax_yields.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    mo.as_html(fig_yields)
    return ax_yields, fig_yields


# --- 3.2 Yield Curve (snapshot) ------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 3.2 Yield Curve — Cross-Sectional Snapshot

    Fetch yields across all maturities for a single date, giving the
    shape of the yield curve.

    **Quant use cases:** Curve shape analysis (normal / inverted / flat),
    Nelson-Siegel / Svensson fitting, relative value trading (butterfly,
    barbell), scenario analysis, swap pricing.
    """)
    return


@app.cell
def _(fi_fetcher):
    yield_curve = fi_fetcher.fetch_yield_curve("2024-12-20")
    yield_curve
    return (yield_curve,)


@app.cell
def _(mo, plt, yield_curve):
    fig_curve, ax_curve = plt.subplots(figsize=(8, 4))
    ax_curve.plot(
        yield_curve["Maturity"],
        yield_curve["Yield"],
        marker="o",
        linewidth=2,
        markersize=8,
    )
    ax_curve.set_title("US Treasury Yield Curve — 20 Dec 2024", fontweight="bold")
    ax_curve.set_xlabel("Maturity")
    ax_curve.set_ylabel("Yield (%)")
    ax_curve.grid(True, alpha=0.3)
    plt.tight_layout()
    mo.as_html(fig_curve)
    return ax_curve, fig_curve


# --- 3.3 Available Maturities --------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ### 3.3 Available Maturities

    List all supported treasury maturities.
    """)
    return


@app.cell
def _(fi_fetcher, mo):
    available = fi_fetcher.get_available_maturities()
    mo.md(f"**Available maturities:** {', '.join(available)}")
    return (available,)


# ---------------------------------------------------------------------------
# Section 4: Use-Case Quick Reference
# ---------------------------------------------------------------------------


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 4. Quantitative Finance Use-Case Quick Reference

    | # | Data Item | Fetcher | Method | Key Use Cases |
    |---|-----------|---------|--------|---------------|
    | 1 | Historical OHLCV (single) | `EquityFetcher` | `fetch_historical()` | VaR, backtesting, volatility modelling, Monte Carlo |
    | 2 | Historical OHLCV (batch) | `EquityFetcher` | `fetch_multiple()` | Portfolio optimisation, correlation, factor models |
    | 3 | Real-time quote | `EquityFetcher` | `fetch_realtime_quote()` | Live P&L, intraday risk monitoring |
    | 4 | Stock info / fundamentals | `EquityFetcher` | `get_info()` | Factor models, fundamental screening, CAPM beta |
    | 5 | Options expirations | `OptionsFetcher` | `get_available_expirations()` | Term structure analysis, roll planning |
    | 6 | Options chain (calls & puts) | `OptionsFetcher` | `fetch_option_chain()` | Vol surface, options pricing, Greeks, hedging |
    | 7 | Options by type (with Greeks) | `OptionsFetcher` | `fetch_greeks()` | Portfolio Greeks, dynamic hedging |
    | 8 | Treasury yields (time series) | `FixedIncomeFetcher` | `fetch_treasury_yields()` | Risk-free rate, bond pricing, interest rate VaR |
    | 9 | Yield curve (snapshot) | `FixedIncomeFetcher` | `fetch_yield_curve()` | Curve fitting, relative value, scenario analysis |
    | 10 | Available maturities | `FixedIncomeFetcher` | `get_available_maturities()` | Discovery / configuration |
    """)
    return


if __name__ == "__main__":
    app.run()
