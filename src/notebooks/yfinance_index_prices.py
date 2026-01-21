import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell
def _():
    import yfinance as yf

    return (yf,)


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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
