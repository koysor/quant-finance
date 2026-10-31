import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import yfinance as yf

    return mo, yf


@app.cell
def _(mo):
    mo.md("""
    This notebook runs locally only, because it fetches live data from Yahoo Finance. Run it with `uv run marimo edit notebooks/local/yfinance_index_prices.py`.
    """)
    return


@app.cell
def _(yf):
    df = yf.download(
        "^GSPC", start="2000-01-01", end="2025-01-01", interval="1d", auto_adjust=True
    )
    return (df,)


@app.cell
def _(df):
    df
    return


if __name__ == "__main__":
    app.run()
