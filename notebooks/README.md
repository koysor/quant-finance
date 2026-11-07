# Marimo notebooks

The browser-ready notebooks are published on [GitHub Pages](https://koysor.github.io/quant-finance/). They run in WebAssembly, so you can view and execute them without setting up a local environment:

| Notebook | Execution |
|----------|-----------|
| Distributions: Normal vs Lognormal | [Open notebook](https://koysor.github.io/quant-finance/distributions_normal_vs_lognormal.html) |
| Simulate Geometric Brownian Motion Paths | [Open notebook](https://koysor.github.io/quant-finance/simulate_geometric_brownian_motion_paths.html) |

Notebooks in `local/` require live market data or the `quant_finance` library and are not published to GitHub Pages. Run them locally with `uv run marimo edit <path>`:

| Notebook | Local command |
|----------|---------------|
| S&P 500 data ingestion | `uv run marimo edit notebooks/local/sp500_data_ingestion.py` |
| Data ingestion examples | `uv run marimo edit notebooks/local/data_ingestion_examples.py` |
| Yahoo Finance index prices | `uv run marimo edit notebooks/local/yfinance_index_prices.py` |
