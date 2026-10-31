---
name: marimo-notebook-helper
description: Create and maintain Marimo notebooks. Use when creating or editing .py files that are Marimo notebooks to ensure reactive data flow integrity and avoid variable redefinition errors.
---

# Marimo Notebook Development

Marimo is a reactive notebook. Each cell's global variables must be unique across the entire notebook.

## Core Rules

### 1. Variable Isolation
Avoid redefinition of variables like `df`, `sym`, `data`, `fig`, `ax` in different cells.

**Good: Prefix loop/local variables with underscores**
```python
@app.cell
def _(multi_data):
    for _sym, _df in multi_data.items():
        # ... do something with _sym, _df
    return
```

**Bad: Redefining global variables**
```python
@app.cell
def _(multi_data):
    for sym, df in multi_data.items(): # FAILS if sym/df defined elsewhere
        # ...
    return
```

### 2. Wrap in Functions
If you need complex logic with many temporary variables, wrap it in a function or a private scope using underscore prefixes.

### 3. Reactive Dependencies
Marimo automatically tracks dependencies based on function arguments. Ensure all required global variables are passed as arguments to the cell function.

### 4. Project Imports
Notebooks in `notebooks/` are published to GitHub Pages and run in the browser, so they can only import `marimo`, `numpy`, `pandas` and `matplotlib`. Notebooks that import `quant_finance` or fetch data go in `notebooks/local/`, as below; no `sys.path` changes are needed.

```python
@app.cell
def _():
    from quant_finance.data_ingestion import EquityFetcher

    return (EquityFetcher,)
```

## Data Ingestion API Reference
For fetching data within notebooks, see [references/data_ingestion_api.md](references/data_ingestion_api.md).
