## Project Overview

This is a Python-based quantitative finance project that provides a collection of tools and examples for financial analysis. The project is structured as a monorepo containing several distinct Streamlit applications, each focused on a different area of quantitative finance, such as options pricing, fixed income analysis, and portfolio management. The applications are designed to be interactive and educational, providing visualizations and demonstrations of financial models and concepts.

The core of the project includes a sophisticated data ingestion module that fetches financial data from external sources like `yfinance`. This module is built with a robust architecture that includes caching (using DuckDB), rate limiting, and retry logic to ensure reliable and efficient data retrieval. The project is fully containerized using Docker, with a `docker-compose.yml` file for orchestrating the different Streamlit applications as separate services.

## Building and Running

### Prerequisites

- Python 3.14
- Docker and Docker Compose

### Local Development

1.  **Install Dependencies:** Dependencies are managed with `pyproject.toml`.
2.  **Run Applications:** You can run each Streamlit application individually using the provided shell scripts:
    ```bash
    # To run the quantitative finance app
    ./launch_quantfinance_streamlit_app.sh

    # To run the options app
    ./launch_options_streamlit_app.sh

    # To run the fixed income app
    ./launch_fixed_income_streamlit_app.sh

    # To run the portfolio management app
    ./launch_portfolio_management_streamlit_app.sh
    ```
    On Windows, run them through Git Bash; [LAUNCH_README.md](LAUNCH_README.md) has a PowerShell command for each.

### Docker

To run all the applications at once using Docker Compose:

```bash
docker-compose up --build
```

The applications will be available at the following ports:
*   **Quant Finance:** `http://localhost:8501`
*   **Options:** `http://localhost:8502`
*   **Fixed Income:** `http://localhost:8503`
*   **Portfolio Management:** `http://localhost:8504`

## Development Conventions

*   **Code Style:** This project uses `ruff` for both code formatting (`ruff format`) and linting (`ruff check`). These are enforced via pre-commit hooks.
*   **Marimo Notebooks:** Marimo is a reactive notebook. Each cell's global variables must be unique across the entire notebook.
    *   **Variable Isolation:** Avoid redefining variables like `df`, `sym`, `data`, `fig`, `ax` in different cells.
    *   **Loop Variables:** Prefix loop and temporary variables with underscores (e.g., `for _sym, _df in multi_data.items():`) to make them local to the cell and prevent conflicts.
    *   **Reactive Flow:** Ensure all required global variables are passed as arguments to the cell functions.
*   **Testing:** Unit tests are in the `tests/` directory. Run them with `uv run pytest tests/ -v --tb=short`. The `tests/test_option_payoffs.py` module provides coverage for option payoff calculations.
*   **CI/CD:** GitHub Actions workflows in `.github/workflows/`:
    *   `code-quality.yml` checks ruff formatting, ruff linting and mypy types, and builds the docs, on every push and pull request.
    *   `tests.yml` runs the pytest suite on every push and pull request.
    *   `deploy-ec2.yml` builds the Docker images and deploys them to EC2.
    *   `deploy-marimo.yml` exports the marimo notebooks to WebAssembly, builds the library docs, and deploys both to GitHub Pages.
    *   `ec2-disk-report.yml` (manual only) reports disk usage on the EC2 host without changing anything.
    *   `ec2-disk-cleanup.yml` (manual only) trims the systemd journal and caps it at 100M, clears the dnf cache, and removes unused Docker volumes except `caddy_data`.
*   **Dependencies:** Project dependencies are managed in the `pyproject.toml` file.