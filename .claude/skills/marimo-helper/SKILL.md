# Marimo Notebook Development Skill

This skill provides expert procedural guidance for creating and maintaining Marimo notebooks within the quantitative finance project. Marimo is a reactive notebook environment where each cell is essentially a Python function, and all global variables must be unique.

## Core Mandates

### 1. Variable Isolation and Redefinition
Marimo will fail if a global variable is defined in multiple cells. To maintain a smooth reactive flow:
- **Loop Variables:** Always prefix loop variables and temporary variables with underscores (e.g., `for _sym, _df in multi_data.items():`) to keep them local to the cell's scope.
- **Common Names:** Avoid using generic names like `df`, `data`, `fig`, `ax`, `sym`, or `symbol` as global variables unless they are meant to be the *sole* definition of that data in the notebook. Prefer descriptive, unique names like `df_aapl` or `multi_data`.

### 2. Reactive Dependency Management
Marimo automatically tracks dependencies by looking at the arguments of the `@app.cell` functions.
- Ensure that if cell B uses a variable defined in cell A, that variable is correctly passed into cell B's function signature.
- Avoid hidden state or side effects that bypass Marimo's dependency graph.

### 3. Execution Environment & Imports
- **Project Path:** Notebooks in `src/notebooks/` must ensure the project root is in `sys.path` to allow importing from `src`.
- **Imports:** Place imports in a dedicated cell at the top of the notebook.

## Workflow: Creating a New Notebook

1. **Initialize Project Path:** Ensure the first cell sets up the project root.
2. **Define Fetchers:** Create a single instance of required fetchers (e.g., `EquityFetcher`).
3. **Surgical Data Retrieval:** Define unique variables for each data fetch (e.g., `df_tsla`).
4. **Visualizations:** Wrap plotting logic in cells that take data variables as dependencies.
5. **Validation:** Ensure no variable names conflict across the entire file.

## Data Ingestion Reference

Refer to `src/data_ingestion/README.md` for full API details. Common fetchers:
- `EquityFetcher()`: `fetch_historical`, `fetch_multiple`, `fetch_realtime_quote`, `get_info`.
- `OptionsFetcher()`: `get_available_expirations`, `fetch_option_chain`, `fetch_greeks`.
- `FixedIncomeFetcher()`: `fetch_treasury_yields`, `fetch_yield_curve`.
