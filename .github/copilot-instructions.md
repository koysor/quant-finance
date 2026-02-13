# Copilot Instructions for quant-finance

> **IMPORTANT:** This repository uses **British English spelling** throughout all code, comments, and documentation. See [Code Conventions](#code-conventions) for details and examples.

## Project Overview

This is an educational quantitative finance repository with four interactive Streamlit applications:
- **Quant Finance** - Stochastic processes, Greeks, volatility modelling, risk management
- **Options** - Options pricing (Black-Scholes, binomial trees, payoff analysis)
- **Fixed Income** - Bond pricing and fixed income securities
- **Portfolio Management** - Modern Portfolio Theory, CAPM, alpha analysis

All applications are built with Streamlit and supported by a modular `src/` library.

## Build, Test & Lint Commands

### Dependencies
- **Install/update:** `uv sync` (uses `pyproject.toml` with locked `uv.lock`)
- **Python version:** 3.13 (enforced in `pyproject.toml` and `.python-version`)

### Testing
```bash
# Run all tests
uv run pytest tests/ -v --tb=short

# Run a single test file
uv run pytest tests/test_option_payoffs.py -v

# Run a specific test
uv run pytest tests/test_option_payoffs.py::test_name -v
```

### Code Quality
```bash
# Format code (auto-fix)
black .

# Lint code (auto-fix enabled via pre-commit)
ruff check . --fix

# Format with ruff
ruff format .

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Running Applications
```bash
# Using provided scripts (preferred)
./launch_quantfinance_streamlit_app.sh
./launch_options_streamlit_app.sh
./launch_fixed_income_streamlit_app.sh
./launch_portfolio_management_streamlit_app.sh

# Or manually
uv run streamlit run app_quant_finance/quantitative_finance.py
uv run streamlit run app_options/options.py
```

### Docker
```bash
# Run all apps via Docker Compose
docker-compose up --build
# Apps available at localhost:8501-8504
```

## Architecture

### Directory Structure

**Application Layer** (`app_*/`)
- Four independent Streamlit apps, each with:
  - Main entry point: `{app_name}.py` (sets page config with `wide` layout)
  - `pages/` - Sub-pages using Streamlit's multi-page app feature
  - Each page is self-contained with its own mathematics and visualisations

**Core Library** (`src/`)
- `data_ingestion/` - Financial data fetching with DuckDB caching and rate limiting
- `options/` - Options pricing models (Black-Scholes, binomial trees, Greeks)
- `portfolio_management/` - Portfolio optimisation and analysis
- `stochastic/` - Stochastic processes (GBM, random walks, Wiener processes)
- `value_at_risk/` - Risk metrics and VaR calculations
- `notebooks/` - Standalone simulation scripts

**Testing** (`tests/`)
- Currently minimal; `test_option_payoffs.py` covers options payoff calculations
- Pytest-based structure with standard fixture patterns

### Key Design Patterns

**Streamlit Pages**
- Each `.py` file in `app_*/pages/` represents one interactive page
- Consistent pattern across pages:
  1. `st.set_page_config(layout="wide")` at top
  2. Markdown title and explanation with LaTeX
  3. Streamlit widgets (sliders, inputs) for interactivity
  4. Mathematical calculations using numpy/scipy
  5. Matplotlib visualisations for output
- Pages are auto-discovered and added to navigation menu (no manual routing)

**Core Modules**
- Stateless functions/classes that perform calculations
- Heavy use of numpy/scipy for numerical methods
- DuckDB for caching financial data fetches
- NetworkX for tree structures (binomial models)

**Data Ingestion**
- Centralised in `src/data_ingestion/` with caching and retry logic
- Uses `yfinance` for market data
- DuckDB backend for efficient querying
- Rate limiting prevents API throttling

## Code Conventions

### Language

**⚠️ ALWAYS use British English spelling in all code, comments, docstrings, and documentation.**

Common conversions:
| American | British |
|----------|---------|
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
| customize | customise |
| recognize | recognise |

This applies to:
- Variable and function names (e.g., `calculate_volatility` not `calculate_volatility`)
- Comments and docstrings
- Markdown documentation and error messages
- User-facing text in Streamlit pages

### Imports & Dependencies
- **Data processing:** numpy, pandas, scipy
- **Financial data:** yfinance
- **Visualisation:** matplotlib, networkx
- **Web framework:** streamlit
- **Development:** black, ruff, pytest, pre-commit (in `[dependency-groups.dev]`)
- **Database:** duckdb for caching, sqlglot for SQL handling

### Code Style
- **Formatting:** Black (line length 88)
- **Linting:** Ruff with auto-fix via pre-commit hooks
- **Comments:** Only where logic needs clarification; avoid redundant comments
- **Type hints:** Encouraged for new code (numpy/scipy compatible)

### Mathematical Code
- Use numpy arrays for numerical operations
- Leverage scipy.stats for distributions (normal, lognormal) and scipy.optimize for fitting
- Document formulas alongside code with LaTeX in docstrings where appropriate
- Validate inputs for edge cases (e.g., non-zero volatility for option pricing)

### Streamlit Page Structure
```python
import streamlit as st
# other imports...

st.set_page_config(layout="wide")
st.markdown("### Page Title")

# Mathematical explanation with LaTeX
st.markdown(r"$$formula$$")

# Interactive widgets
param = st.slider("Parameter", min_value, max_value)

# Calculations
result = calculate(param)

# Visualisation
fig, ax = plt.subplots()
ax.plot(...)
st.pyplot(fig)
```

### Data Ingestion Pattern
- Cache data fetches with DuckDB to avoid redundant API calls
- Use `yfinance` for historical/current market data
- Handle rate limiting with exponential backoff
- Return pandas DataFrames for consistency with downstream processing

## CI/CD

**GitHub Actions Workflows:**
- **code-quality.yml** - Validates Black formatting and Ruff linting on push/PR
- **tests.yml** - Runs pytest suite on push/PR to main
- **deploy-ec2.yml** - Deploys applications to AWS EC2
- **deploy-marimo.yml** - Deploys Marimo notebooks to GitHub Pages

Pre-commit hooks run locally on commit:
- Black (formatting)
- Ruff (linting with auto-fix)
- Detect-secrets (prevents credential commits)

## Important Notes

- **Limited Test Coverage:** While a testing framework is in place (using `pytest`, as seen in `tests/` and `.github/workflows/tests.yml`), test coverage is currently limited to option payoffs. Adding tests is strongly encouraged for new features and existing modules.
- **Docker images** exclude dev dependencies; only runtime packages are installed
- **Data caching** is critical for performance; always check `src/data_ingestion/` before adding new data fetching logic
- **Streamlit state management** can be tricky; use `st.session_state` carefully and document non-obvious state dependencies
- **Port mappings for Docker:** 8501 (Quant), 8502 (Options), 8503 (Fixed Income), 8504 (Portfolio)
