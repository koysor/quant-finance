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
Always ensure the project root is in `sys.path` for notebooks located in `src/notebooks/`.

```python
@app.cell
def _():
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return
```

## Data Ingestion API Reference
For fetching data within notebooks, see [references/data_ingestion_api.md](references/data_ingestion_api.md).
