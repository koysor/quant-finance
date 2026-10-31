# quant-finance

Python implementations of quantitative finance models: a tested pricing and market data library, with interactive Streamlit apps and browser-based notebooks built around it.

## Repository Layout

| Path | Contents |
|------|----------|
| [`projects/`](projects/README.md) | Self-contained projects, each with a question, results and limitations |
| `src/quant_finance/` | Installable library: `pricing`, `options` and [`data_ingestion`](src/quant_finance/data_ingestion/README.md) |
| `app_*/` | Streamlit apps for quantitative finance, options, fixed income and portfolio management |
| `notebooks/` | Marimo notebooks exported to WebAssembly for GitHub Pages; `notebooks/local/` holds those that need live data |
| `tests/` | pytest suite covering Black-Scholes pricing, option payoffs and the DuckDB cache |
| `docker/` | Container images and the production deployment configuration |

## Getting Started

```bash
uv sync                                # Install the library and its dependencies
uv run pytest tests/                   # Run the tests
uv run mypy src/quant_finance          # Check types
./launch_options_streamlit_app.sh      # Launch an app
```

## Key Technologies

### Data and Numerical Processing

| Library | Purpose |
|---------|---------|
| **NumPy** | Array operations, random number generation for Monte Carlo methods, linear algebra for portfolio optimisation |
| **pandas** | DataFrame structures for financial time series, rolling window calculations, data cleaning |
| **SciPy** | Statistical distributions for option pricing, optimisation for portfolio weights, yield curve interpolation |
| **DuckDB** | Embedded OLAP database for efficient analytical queries on financial data |

### Market Data and Visualisation

| Library | Purpose |
|---------|---------|
| **yfinance** | Historical price data, real-time quotes, and fundamental data from Yahoo Finance |
| **Matplotlib** | Financial charts, payoff diagrams, distribution plots, volatility surfaces |
| **NetworkX** | Graph visualisation for binomial tree option pricing models |
| **Streamlit** | Interactive web dashboards with real-time parameter adjustment |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Jupyter / Marimo** | Interactive notebook environments for exploratory analysis |
| **pytest** | Testing framework for code quality |
| **mypy** | Static type checking for the library |
| **Black / Ruff** | Code formatting and linting |
| **pre-commit** | Git hooks for automated code quality checks |

## Live Streamlit Applications

This project features several Streamlit applications, providing interactive access to various quantitative finance tools.

* **AWS EC2 Deployments:** The following applications are deployed on an AWS EC2 instance with HTTPS via Caddy reverse proxy.

  * **Quant Finance:** [https://koysor.duckdns.org/quant/](https://koysor.duckdns.org/quant/)
  * **Options:** [https://koysor.duckdns.org/options/](https://koysor.duckdns.org/options/)
  * **Fixed Income:** [https://koysor.duckdns.org/fixed-income/](https://koysor.duckdns.org/fixed-income/)
  * **Portfolio Management:** [https://koysor.duckdns.org/portfolio/](https://koysor.duckdns.org/portfolio/)
  * **Maths Python:** [https://koysor.duckdns.org/maths/](https://koysor.duckdns.org/maths/)

## App Availability Monitoring

Uptime and availability for all live Streamlit applications is tracked via UptimeRobot. View the current status and historical uptime at:

**Status Page:** [https://stats.uptimerobot.com/75Jq7PxIkL](https://stats.uptimerobot.com/75Jq7PxIkL)

## Interactive Marimo Notebooks

Interactive Python notebooks are available via GitHub Pages at **https://koysor.github.io/quant-finance/**

These notebooks run entirely in your browser using WebAssembly (no server required) and allow you to view, edit, and execute the code directly:

* [Distributions: Normal vs Lognormal](https://koysor.github.io/quant-finance/distributions_normal_vs_lognormal.html)
* [Simulate Geometric Brownian Motion Paths](https://koysor.github.io/quant-finance/simulate_geometric_brownian_motion_paths.html)

Notebooks that fetch live market data can't run in the browser, so they are in `notebooks/local/`. Run one with:

```bash
uv run marimo edit notebooks/local/sp500_data_ingestion.py
```

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality standards automatically before each commit.

### Configured Hooks

| Hook | Version | Purpose |
|------|---------|---------|
| **detect-secrets** | 1.5.0 | Prevents secrets from being committed to the repository |
| **Black** | 26.1.0 | Code formatting - ensures consistent Python style |
| **Ruff** | 0.14.14 | Linting with auto-fix - catches errors and style issues |
| **Ruff Format** | 0.14.14 | Additional formatting checks |

### Installation

To install the pre-commit hooks locally:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the hooks (one-time setup)
pre-commit install
```

### Usage

Once installed, hooks run automatically on `git commit`. You can also run them manually:

```bash
# Run on staged files only
pre-commit run

# Run on all files in the repository
pre-commit run --all-files

# Run a specific hook
pre-commit run black --all-files
```

### Skipping Hooks

In rare cases where you need to bypass the hooks (not recommended):

```bash
git commit --no-verify -m "commit message"
```