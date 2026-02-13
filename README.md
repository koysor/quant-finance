# quant-finance

This repository, `quant-finance`, serves as a comprehensive collection of Python code examples and tools for various quantitative finance applications. It encompasses modules dedicated to key areas such as fixed income analysis, options pricing and strategies, and portfolio management. The project aims to provide practical implementations of financial models and concepts, making complex quantitative methods accessible and understandable through code.

A significant feature of this repository is its integration with Streamlit, enabling users to interact with many of the quantitative finance tools via a user-friendly web application. This allows for immediate visualization and experimentation with financial models, from binomial trees for option pricing to Monte Carlo simulations for stock price forecasting. The Streamlit applications are structured around different financial domains, offering dedicated interfaces for each.

Beyond the interactive applications, the repository includes robust data ingestion capabilities, ensuring that the financial models can be fed with relevant and timely data. It also contains extensive unit tests to maintain code quality and accuracy, along with development configurations and Docker files to facilitate a consistent development and deployment environment. This makes `quant-finance` a valuable resource for both learning and applying quantitative finance principles.

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
| **Black / Ruff** | Code formatting and linting |
| **pre-commit** | Git hooks for automated code quality checks |

## Live Streamlit Applications

This project features several Streamlit applications, providing interactive access to various quantitative finance tools.

* **AWS EC2 Deployments:** For more specialised applications, the following are deployed on an AWS EC2 instance.

  * **Quant Finance:** http://koysor.duckdns.org/quant/
  * **Options:** http://koysor.duckdns.org/options/
  * **Fixed Income:** http://koysor.duckdns.org/fixed-income/
  * **Portfolio Management:** http://koysor.duckdns.org/portfolio/

## App Availability Monitoring

Uptime and availability for all live Streamlit applications is tracked via UptimeRobot. View the current status and historical uptime at:

**[Status Page](https://stats.uptimerobot.com/75Jq7PxIkL)**

## Interactive Marimo Notebooks

Interactive Python notebooks are available via GitHub Pages at **https://koysor.github.io/quant-finance/**

These notebooks run entirely in your browser using WebAssembly (no server required) and allow you to view, edit, and execute the code directly:

* [Distributions: Normal vs Lognormal](https://koysor.github.io/quant-finance/distributions_normal_vs_lognormal.html)
* [Simulate Geometric Brownian Motion Paths](https://koysor.github.io/quant-finance/simulate_geometric_brownian_motion_paths.html)
* [S&amp;P 500 Data Ingestion](https://koysor.github.io/quant-finance/sp500_data_ingestion.html)
* [YFinance Index Prices](https://koysor.github.io/quant-finance/yfinance_index_prices.html)

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality standards automatically before each commit.

### Configured Hooks

| Hook | Version | Purpose |
|------|---------|---------|
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