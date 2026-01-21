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
    return mo, plt


@app.cell
def _(mo):
    mo.md(
        """
    # S&P 500 Data Fetcher

    This notebook uses the `data_ingestion` module to fetch S&P 500 historical data
    with automatic caching, rate limiting, and error handling.
    """
    )
    return


@app.cell
def _(mo):
    # Date input controls
    start_date = mo.ui.date(
        value="2020-01-01", label="Start Date", start="2000-01-01", stop="2025-12-31"
    )

    end_date = mo.ui.date(
        value="2025-12-31", label="End Date", start="2000-01-01", stop="2025-12-31"
    )

    mo.md(
        f"""
        ## Select Date Range

        {start_date} {end_date}
        """
    )
    return end_date, start_date


@app.cell
def _(mo):
    # Additional controls
    use_cache = mo.ui.checkbox(value=True, label="Use cached data (recommended)")

    interval = mo.ui.dropdown(
        options=["1d", "1wk", "1mo"], value="1d", label="Data Interval"
    )

    mo.md(
        f"""
        ## Options

        {use_cache}

        {interval}
        """
    )
    return interval, use_cache


@app.cell
def _(end_date, interval, mo, start_date, use_cache):
    # Fetch button
    fetch_button = mo.ui.run_button(label="Fetch S&P 500 Data")

    mo.md(
        f"""
        ---

        **Selected range:** {start_date.value} to {end_date.value}
        **Interval:** {interval.value}
        **Use cache:** {use_cache.value}

        {fetch_button}
        """
    )
    return (fetch_button,)


@app.cell
def _():
    # Import the data ingestion module
    from src.data_ingestion import EquityFetcher, FetchError

    return EquityFetcher, FetchError


@app.cell
def _(
    EquityFetcher,
    FetchError,
    end_date,
    fetch_button,
    interval,
    mo,
    start_date,
    use_cache,
):
    # Fetch data when button is clicked
    df_sp500 = None
    error_msg = None
    fetch_status = None

    if fetch_button.value:
        try:
            fetcher = EquityFetcher()
            df_sp500 = fetcher.fetch_historical(
                symbol="^GSPC",
                start_date=start_date.value,
                end_date=end_date.value,
                interval=interval.value,
                use_cache=use_cache.value,
            )

            fetch_status = mo.md(
                f"✓ Successfully fetched {len(df_sp500)} trading days of S&P 500 data"
            )

        except FetchError as e:
            error_msg = str(e)
            fetch_status = mo.md(f"❌ Error fetching data: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            fetch_status = mo.md(f"❌ Unexpected error: {error_msg}")

    fetch_status
    return (df_sp500,)


@app.cell
def _(df_sp500, fetch_button, mo):
    # Display summary statistics
    summary_output = None
    if fetch_button.value and df_sp500 is not None:
        summary_output = mo.md(
            f"""
            ## Data Summary

            **Total trading days:** {len(df_sp500)}
            **Date range:** {df_sp500.index[0].strftime("%Y-%m-%d")} to {df_sp500.index[-1].strftime("%Y-%m-%d")}

            ### Closing Price Statistics

            - **Latest Close:** ${df_sp500["Close"].iloc[-1]:,.2f}
            - **Mean Close:** ${df_sp500["Close"].mean():,.2f}
            - **Min Close:** ${df_sp500["Close"].min():,.2f}
            - **Max Close:** ${df_sp500["Close"].max():,.2f}
            - **Std Dev:** ${df_sp500["Close"].std():,.2f}
            """
        )

    summary_output
    return


@app.cell
def _(df_sp500, fetch_button):
    # Display the data table
    data_display = None
    if fetch_button.value and df_sp500 is not None:
        # Show first and last 10 rows
        data_display = df_sp500

    data_display
    return


@app.cell
def _(df_sp500, fetch_button, mo, plt):
    # Plot closing prices
    chart_output = None
    if fetch_button.value and df_sp500 is not None:
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(df_sp500.index, df_sp500["Close"], linewidth=1.5, color="#1f77b4")
        ax.set_title("S&P 500 Closing Prices", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=11)
        ax.set_ylabel("Price ($)", fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()

        chart_output = mo.md(
            f"""
            ## Visualization

            {mo.as_html(fig)}
            """
        )

    chart_output
    return


@app.cell
def _(df_sp500, fetch_button, mo):
    # Export options
    export_info = None
    if fetch_button.value and df_sp500 is not None:
        export_info = mo.md(
            """
            ## Export Data

            You can export the fetched data using:

            ```python
            # Export to CSV
            df_sp500.to_csv('sp500_data.csv')

            # Export to Excel
            df_sp500.to_excel('sp500_data.xlsx')

            # Get just closing prices
            closing_prices = df_sp500['Close']
            ```
            """
        )

    export_info
    return


@app.cell
def _(df_sp500, mo):
    _df = mo.sql(
        """
        select * from df_sp500
        """
    )
    return


if __name__ == "__main__":
    app.run()
