# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a quantitative finance educational repository that demonstrates Python implementations of financial models through interactive Streamlit web applications. The project contains four main applications:

1. **Quantitative Finance App** (`app_quant_finance/`) - Educational content covering stochastic processes, Greeks, volatility modelling, risk management, and mathematical finance concepts
2. **Options App** (`app_options/`) - Focused on options pricing models including binomial trees, Black-Scholes, and option payoffs
3. **Fixed Income App** (`app_fixed_income/`) - Bond pricing and fixed income securities
4. **Portfolio Management App** (`app_portfolio_management/`) - Modern Portfolio Theory, CAPM, and alpha analysis

## Architecture

The codebase follows a modular structure:

- **`app_quant_finance/`** - Main Streamlit app for quantitative finance concepts
  - `quantitative_finance.py` - Main entry point
  - `pages/` - Individual Streamlit pages for different topics (Greeks, Black-Scholes, volatility, etc.)

- **`app_options/`** - Streamlit app focused on options
  - `options.py` - Main entry point
  - `pages/` - Options-specific pages (binomial model, option payoffs, put-call parity, volatility spreads)

- **`app_fixed_income/`** - Streamlit app for fixed income and bonds
  - `fixed_income.py` - Main entry point
  - `pages/` - Bond pricing and fixed income pages

- **`app_portfolio_management/`** - Streamlit app for portfolio management
  - `portfolio_management.py` - Main entry point
  - `pages/` - MPT, CAPM, and alpha analysis pages

- **`src/`** - Core Python modules and notebooks
  - `notebooks/` - Python scripts for simulations and data analysis (GBM, distributions, yfinance)
  - `options/`, `portfolio_management/`, `stochastic/`, `value_at_risk/` - Topic-specific modules

## Development Commands

### Running Applications
```bash
# Quantitative Finance Streamlit app
./launch_quantfinance_streamlit_app.sh
# or manually:
source .venv/bin/activate && uv run streamlit run app_quant_finance/quantitative_finance.py

# Options Streamlit app
./launch_options_streamlit_app.sh
# or manually:
source .venv/bin/activate && uv run streamlit run app_options/options.py

# Fixed Income Streamlit app
./launch_fixed_income_streamlit_app.sh
# or manually:
source .venv/bin/activate && uv run streamlit run app_fixed_income/fixed_income.py

# Portfolio Management Streamlit app
./launch_portfolio_management_streamlit_app.sh
# or manually:
source .venv/bin/activate && uv run streamlit run app_portfolio_management/portfolio_management.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Pre-commit hooks (automatically runs black and ruff on commit)
pre-commit install        # Setup hooks (already done)
pre-commit run --all-files  # Run hooks manually on all files
```

### CI/CD
- **GitHub Actions** workflows:
  - `code-quality.yml` - Validates black formatting and ruff linting on push/PR
  - `tests.yml` - Runs pytest on push/PR
  - `deploy-ec2.yml` - Builds Docker images and deploys to EC2
  - `deploy-marimo.yml` - Exports marimo notebooks to WASM and deploys to GitHub Pages
- **Pre-commit hooks** - Local code quality enforcement (detect-secrets, black, ruff)

### Environment
- Python 3.13 required (see `.python-version`)
- Virtual environment in `.venv/`
- Dependencies managed via `pyproject.toml` with uv lock file

## Key Dependencies

### Data and Numerical Processing

- **numpy** - Fundamental numerical computing library (transitive dependency via scipy/pandas)
  - Array operations for price simulations and time series
  - Random number generation for Monte Carlo methods
  - Linear algebra for portfolio optimisation
  - Statistical functions for financial metrics

- **pandas** - Data manipulation and analysis
  - DataFrame structures for financial time series data
  - Date/time handling for market data
  - Rolling window calculations for moving averages and volatility
  - Data cleaning and transformation for market data feeds

- **scipy** - Scientific computing and advanced numerical methods
  - `scipy.stats` - Statistical distributions (normal, log-normal) for option pricing and VaR
  - `scipy.optimize` - Optimisation algorithms for portfolio weights and implied volatility
  - `scipy.interpolate` - Yield curve interpolation for fixed income
  - `scipy.integrate` - Numerical integration for pricing models

- **duckdb** - Embedded analytical database
  - In-process OLAP database for efficient data queries
  - SQL interface for financial data analysis
  - Columnar storage optimised for analytical workloads

### Market Data

- **yfinance** - Yahoo Finance market data API
  - Historical price data retrieval
  - Real-time quotes for stocks, ETFs, and indices
  - Fundamental data for equities

### Visualisation

- **matplotlib** - Plotting and visualisations
  - Financial charts (price series, payoff diagrams)
  - Distribution plots for risk analysis
  - Surface plots for volatility surfaces

- **networkx** - Graph theory library
  - Binomial tree visualisation for options pricing
  - Tree structure representation for discrete models

- **streamlit** - Web application framework
  - Interactive dashboards for financial models
  - Real-time parameter adjustment via widgets
  - Built-in charting capabilities

### Development and Notebooks

- **jupyter** / **marimo** - Interactive notebook environments
- **pytest** - Testing framework
- **black** - Code formatting
- **ruff** - Linting
- **pre-commit** - Git hooks for code quality (auto-runs black and ruff on commit)

## Code Patterns

- Each Streamlit page follows a similar pattern:
  - Import streamlit and required libraries
  - Set page config with wide layout
  - Add markdown headers and explanatory text
  - Include mathematical formulations using LaTeX
  - Provide interactive examples and visualisations

- Pages are educational-focused, combining theory with practical Python implementations
- Mathematical concepts are explained with both LaTeX formulations and code examples

<h2>Language and Spelling</h2>

**Always use British English spelling** in all code, comments, docstrings, and documentation. Common examples:

| American (avoid) | British (use) |
|------------------|---------------|
| behavior | behaviour |
| color | colour |
| optimize | optimise |
| realize | realise |
| analyze | analyse |
| center | centre |
| modeling | modelling |
| visualize | visualise |
| initialize | initialise |
| normalize | normalise |