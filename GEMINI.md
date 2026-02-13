## Project Overview

This is a Python-based quantitative finance project that provides a collection of tools and examples for financial analysis. The project is structured as a monorepo containing several distinct Streamlit applications, each focused on a different area of quantitative finance, such as options pricing, fixed income analysis, and portfolio management. The applications are designed to be interactive and educational, providing visualizations and demonstrations of financial models and concepts.

The core of the project includes a sophisticated data ingestion module that fetches financial data from external sources like `yfinance`. This module is built with a robust architecture that includes caching (using DuckDB), rate limiting, and retry logic to ensure reliable and efficient data retrieval. The project is fully containerized using Docker, with a `docker-compose.yml` file for orchestrating the different Streamlit applications as separate services.

## Building and Running

### Prerequisites

- Python 3.13
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

*   **Code Style:** This project uses `black` for code formatting and `ruff` for linting. These are enforced via pre-commit hooks.
*   **Testing:** There are currently no tests in the `tests/` directory. This is an area for future improvement.
*   **CI/CD:** A GitHub Actions workflow (`.github/workflows/code-quality.yml`) automatically checks for code quality on every push and pull request to the `main` branch. Additionally, `.github/workflows/tests.yml` runs unit tests.
*   **Dependencies:** Project dependencies are managed in the `pyproject.toml` file.
