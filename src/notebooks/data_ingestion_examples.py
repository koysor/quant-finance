import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import sys
    from pathlib import Path
    from datetime import datetime, timedelta

    # Add project root to path for src imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.data_ingestion import (
        EquityFetcher,
        OptionsFetcher,
        FixedIncomeFetcher,
        FetchError,
    )

    # Initialize fetchers
    equity_fetcher = EquityFetcher()
    options_fetcher = OptionsFetcher()
    fi_fetcher = FixedIncomeFetcher()

    # Dynamic date ranges
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date_3m = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    return (
        EquityFetcher,
        FetchError,
        FixedIncomeFetcher,
        OptionsFetcher,
        datetime,
        end_date,
        equity_fetcher,
        fi_fetcher,
        mo,
        options_fetcher,
        plt,
        project_root,
        start_date_3m,
        sys,
        timedelta,
    )


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


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 1. Equity Data (`EquityFetcher`)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### 1.1 Historical OHLCV — Single Symbol

    Fetch daily Open, High, Low, Close, Volume data for Apple (AAPL).

    **Quant use cases:** VaR, backtesting, volatility modelling, Monte Carlo simulation.
    """)
    return


@app.cell
def _(end_date, equity_fetcher, mo, start_date_3m):
    try:
        df_aapl = equity_fetcher.fetch_historical(
            symbol="AAPL",
            start_date=start_date_3m,
            end_date=end_date,
            interval="1d",
        )
        _status = mo.md(f"Fetched **{len(df_aapl)} rows** of daily AAPL data.")
    except Exception as e:
        df_aapl = None
        _status = mo.md(f"**Error fetching AAPL:** {e}")

    _status
    return (df_aapl,)


@app.cell
def _(df_aapl):
    if df_aapl is not None:
        return df_aapl.head(10)
    return


@app.cell
def _(df_aapl, mo, plt, start_date_3m):
    if df_aapl is not None:
        fig_aapl, ax_aapl = plt.subplots(figsize=(10, 4))
        ax_aapl.plot(df_aapl.index, df_aapl["Close"], linewidth=1.5)
        ax_aapl.set_title(
            f"AAPL Daily Close — {start_date_3m} to Today", fontweight="bold"
        )
        ax_aapl.set_ylabel("Price ($)")
        ax_aapl.grid(True, alpha=0.3)
        ax_aapl.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        _out = mo.as_html(fig_aapl)
    else:
        _out = mo.md("No data to plot.")
    _out
    return (ax_aapl, fig_aapl)


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
def _(end_date, equity_fetcher, mo, start_date_3m):
    symbols = ["AAPL", "MSFT", "GOOGL"]
    try:
        multi_data = equity_fetcher.fetch_multiple(
            symbols=symbols,
            start_date=start_date_3m,
            end_date=end_date,
        )

        for _sym, _df in multi_data.items():
            mo.output.append(mo.md(f"**{_sym}**: {len(_df)} rows"))
    except Exception as e:
        multi_data = {}
        mo.output.append(mo.md(f"**Error fetching batch data:** {e}"))
    return (multi_data,)


@app.cell
def _(mo, multi_data, plt, start_date_3m):
    if multi_data:
        fig_multi, ax_multi = plt.subplots(figsize=(10, 4))
        for _sym, _df in multi_data.items():
            # Normalise to 100 at start for comparison
            _normalised = _df["Close"] / _df["Close"].iloc[0] * 100
            ax_multi.plot(_normalised.index, _normalised, label=_sym, linewidth=1.5)
        ax_multi.set_title(
            f"Normalised Close Prices — {start_date_3m} to Today", fontweight="bold"
        )
        ax_multi.set_ylabel("Indexed (100 = start)")
        ax_multi.legend()
        ax_multi.grid(True, alpha=0.3)
        ax_multi.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        _out = mo.as_html(fig_multi)
    else:
        _out = mo.md("No multi-symbol data to plot.")
    _out
    return (ax_multi, fig_multi)


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
    try:
        quote = equity_fetcher.fetch_realtime_quote("AAPL")

        _out = mo.md(f"""
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
    except Exception as e:
        _out = mo.md(f"**Error fetching real-time quote:** {e}")
    _out
    return (quote,)


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
    try:
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
                f"{info.get('52WeekChange', 0):.2%}"
                if info.get("52WeekChange")
                else "N/A"
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
        _out = mo.md(f"""
        | Field | Value |
        |-------|-------|
        {_rows}
        """)
    except Exception as e:
        _out = mo.md(f"**Error fetching fundamentals:** {e}")
    _out
    return (info,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 2. Options Data (`OptionsFetcher`)
    """)
    return


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
    try:
        expirations = options_fetcher.get_available_expirations("AAPL")

        _out = mo.md(f"""
        **AAPL** has **{len(expirations)}** available option expirations.

        First 10: {", ".join(expirations[:10])}
        """)
    except Exception as e:
        expirations = []
        _out = mo.md(f"**Error fetching expirations:** {e}")
    _out
    return (expirations,)


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
    if expirations:
        try:
            # Use the nearest available expiration
            _exp = expirations[0]
            calls, puts = options_fetcher.fetch_option_chain("AAPL", _exp)

            _out = mo.md(f"""
            Expiration **{_exp}**: **{len(calls)}** calls, **{len(puts)}** puts
            """)
        except Exception as e:
            calls, puts = None, None
            _out = mo.md(f"**Error fetching option chain:** {e}")
    else:
        calls, puts = None, None
        _out = mo.md("No expirations available.")
    _out
    return calls, puts


@app.cell
def _(calls, mo):
    if calls is not None:
        mo.output.append(mo.md("**Call options (first 10 rows):**"))
        return calls[
            [
                "Strike",
                "Last",
                "Bid",
                "Ask",
                "Volume",
                "OpenInterest",
                "ImpliedVolatility",
            ]
        ].head(10)
    return


@app.cell
def _(mo, puts):
    if puts is not None:
        mo.output.append(mo.md("**Put options (first 10 rows):**"))
        return puts[
            [
                "Strike",
                "Last",
                "Bid",
                "Ask",
                "Volume",
                "OpenInterest",
                "ImpliedVolatility",
            ]
        ].head(10)
    return


@app.cell
def _(calls, mo, plt, puts):
    if calls is not None and puts is not None:
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
        _out = mo.as_html(fig_iv)
    else:
        _out = mo.md("No option data for IV plot.")
    _out
    return (ax_iv, fig_iv)


@app.cell
def _(mo):
    mo.md("""
    ### 2.3 Options by Type (with available Greeks)

    Fetch only calls or puts for a given expiration. yfinance provides
    implied volatility natively.

    **Quant use cases:** Portfolio Greeks aggregation, dynamic hedging,
    risk limits monitoring.
    """)
    return


@app.cell
def _(expirations, mo, options_fetcher):
    if expirations:
        try:
            _exp = expirations[0]
            greeks_calls = options_fetcher.fetch_greeks(
                "AAPL", _exp, option_type="call"
            )
            _out = greeks_calls[
                ["Strike", "Last", "Bid", "Ask", "ImpliedVolatility"]
            ].head(10)
        except Exception as e:
            _out = mo.md(f"**Error fetching Greeks data:** {e}")
    else:
        _out = mo.md("No expirations available.")
    _out
    return (greeks_calls,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 3. Fixed Income Data (`FixedIncomeFetcher`)
    """)
    return


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
def _(end_date, fi_fetcher, mo, start_date_3m):
    try:
        yields_df = fi_fetcher.fetch_treasury_yields(
            maturities=["3M", "5Y", "10Y", "30Y"],
            start_date=start_date_3m,
            end_date=end_date,
        )

        _status = mo.md(f"Fetched **{len(yields_df)} rows** of treasury yield data.")
    except Exception as e:
        yields_df = None
        _status = mo.md(f"**Error fetching yields:** {e}")

    _status
    return (yields_df,)


@app.cell
def _(yields_df):
    if yields_df is not None:
        return yields_df.head(10)
    return


@app.cell
def _(mo, plt, start_date_3m, yields_df):
    if yields_df is not None:
        fig_yields, ax_yields = plt.subplots(figsize=(10, 4))
        for col in yields_df.columns:
            ax_yields.plot(yields_df.index, yields_df[col], label=col, linewidth=1.5)
        ax_yields.set_title(
            f"US Treasury Yields — {start_date_3m} to Today", fontweight="bold"
        )
        ax_yields.set_ylabel("Yield (%)")
        ax_yields.legend()
        ax_yields.grid(True, alpha=0.3)
        ax_yields.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        _out = mo.as_html(fig_yields)
    else:
        _out = mo.md("No yield data to plot.")
    _out
    return (ax_yields, fig_yields)


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
def _(end_date, fi_fetcher, mo):
    try:
        # Fetch for the latest available date
        yield_curve = fi_fetcher.fetch_yield_curve(end_date)
        _out = yield_curve
    except Exception as e:
        yield_curve = None
        _out = mo.md(f"**Error fetching yield curve:** {e}")
    _out
    return (yield_curve,)


@app.cell
def _(mo, plt, yield_curve):
    if yield_curve is not None:
        fig_curve, ax_curve = plt.subplots(figsize=(8, 4))
        ax_curve.plot(
            yield_curve["Maturity"],
            yield_curve["Yield"],
            marker="o",
            linewidth=2,
            markersize=8,
        )
        ax_curve.set_title("US Treasury Yield Curve — Latest", fontweight="bold")
        ax_curve.set_xlabel("Maturity")
        ax_curve.set_ylabel("Yield (%)")
        ax_curve.grid(True, alpha=0.3)
        plt.tight_layout()
        _out = mo.as_html(fig_curve)
    else:
        _out = mo.md("No yield curve data to plot.")
    _out
    return (ax_curve, fig_curve)


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
    return


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
