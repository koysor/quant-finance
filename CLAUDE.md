# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a quantitative finance educational repository that demonstrates Python implementations of financial models through interactive Streamlit web applications. The project contains two main applications:

1. **Quantitative Finance App** (`app_quant_finance/`) - Educational content covering stochastic processes, Greeks, volatility modeling, risk management, and mathematical finance concepts
2. **Options App** (`app_options/`) - Focused on options pricing models including binomial trees, Black-Scholes, and option payoffs

## Architecture

The codebase follows a modular structure:

- **`app_quant_finance/`** - Main Streamlit app for quantitative finance concepts
  - `quantitative_finance.py` - Main entry point
  - `pages/` - Individual Streamlit pages for different topics (Greeks, Black-Scholes, volatility, etc.)

- **`app_options/`** - Streamlit app focused on options
  - `options.py` - Main entry point
  - `pages/` - Options-specific pages (binomial model, pricing, payoffs, etc.)

- **`src/`** - Core Python modules (currently empty directories for future expansion)
  - `options/`, `portfolio_management/`, `stochastic/`, `value_at_risk/`

## Development Commands

### Running Applications
```bash
# Quantitative Finance Streamlit app
./launch_quantfinance_streamlit_app.sh
# or manually:
source .venv/bin/activate && streamlit run app_quant_finance/quantitative_finance.py

# Options Streamlit app
./launch_options_streamlit_app.sh
# or manually:
source .venv/bin/activate && streamlit run app_options/options.py
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
- **GitHub Actions** - Automated code quality checks on push/PR
- **Pre-commit hooks** - Local code quality enforcement
- Workflow validates black formatting and ruff linting

### Environment
- Python 3.10+ required (see `.python-version`)
- Virtual environment in `.venv/`
- Dependencies managed via `pyproject.toml` with uv lock file

## Key Dependencies

- **streamlit** - Web application framework
- **matplotlib** - Plotting and visualizations
- **pandas** - Data manipulation
- **scipy** - Scientific computing
- **networkx** - Graph theory (used for binomial trees)
- **black** - Code formatting
- **ruff** - Linting
- **pre-commit** - Git hooks for code quality (auto-runs black and ruff on commit)

## Code Patterns

- Each Streamlit page follows a similar pattern:
  - Import streamlit and required libraries
  - Set page config with wide layout
  - Add markdown headers and explanatory text
  - Include mathematical formulations using LaTeX
  - Provide interactive examples and visualizations

- Pages are educational-focused, combining theory with practical Python implementations
- Mathematical concepts are explained with both LaTeX formulations and code examples