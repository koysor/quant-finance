---
name: new-notebook
description: Create an educational marimo notebook in notebooks/ that is published to GitHub Pages and runs in the browser
disable-model-invocation: true
argument-hint: [notebook-name] [topic]
---

Create an educational marimo notebook following the quantitative finance project conventions.

**Notebook name:** $0 (snake_case filename without .py extension, e.g. `put_call_parity`)
**Topic:** $ARGUMENTS

Create the file at `notebooks/$0.py`. Use `notebooks/distributions_normal_vs_lognormal.py` and `notebooks/simulate_geometric_brownian_motion_paths.py` as reference examples. Follow the general marimo rules in the shared `koysor-skills:marimo-helper` skill (unique global names, `_`-prefixed temporaries, dependencies through cell arguments).

## Browser constraints

Notebooks in `notebooks/` are exported to WebAssembly by `.github/workflows/deploy-marimo.yml` and run in Pyodide, so:

1. **Imports** — only `marimo`, `numpy`, `pandas`, `matplotlib`, `scipy` and `sympy` (Pyodide ships all six). `tests/test_notebooks.py` fails on anything else, including `quant_finance` and the standard library (e.g. `math`). If the topic needs `quant_finance` or live data, stop and put the notebook in `notebooks/local/` instead.
2. **No network, files or databases** — generate data with `numpy` (seed it, e.g. `rng = np.random.default_rng(42)`) or define small datasets inline.
3. **Self-contained maths** — implement the model in the notebook, since `quant_finance` is unavailable. Use `scipy.stats` for distributions (e.g. `norm.cdf` in Black-Scholes) and `sympy` for symbolic derivations such as Greeks.
4. **Light computation** — keep simulations to a size that renders in a browser in a few seconds (around 10,000 paths × 252 steps at most); the notebook must also run as a script within 120 seconds for the test.

## Notebook structure

1. **Header** — `import marimo`, `__generated_with` set to the installed marimo version (`uv run marimo --version`), and `app = marimo.App(width="full")`.
2. **Imports cell** — one cell at the top importing `marimo as mo` and the packages needed, returning them.
3. **Title and introduction** — `mo.md(r"""# Title ...""")` explaining the concept, why it matters in finance, and what the reader will see.
4. **Mathematical formulation** — LaTeX in `mo.md` with raw strings (`$...$` inline, `$$...$$` display). Define every symbol.
5. **Implementation** — functions with NumPy-style docstrings, vectorised where possible. Call `mo.show_code()` in cells whose code is part of the lesson, so it also shows in the read-only view.
6. **Interactive example** — `mo.ui.slider` / `mo.ui.number` / `mo.ui.dropdown` widgets for the key parameters, each in its own cell or grouped with `mo.hstack` / `mo.vstack`, with sensible ranges (e.g. volatility starting above zero). Plots and statistics read `widget.value` so they update reactively.
7. **Visualisation** — create and display each matplotlib figure in a single cell, ending the cell with the figure (or `plt.gca()`); label axes and titles, and use `fig.tight_layout()`.
8. **Interpretation** — `mo.md(...).callout(kind="info")` for key insights, and a short summary of what the reader should take away. Compare simulated results with theory where possible.
9. **Footer** — `if __name__ == "__main__": app.run()`.

Use **British English spelling** throughout (e.g. modelling, visualise, normalise, colour).

## Publishing

The deploy workflow picks up every `notebooks/*.py` automatically, publishing `$0.html` (view) and `$0-edit.html` (edit code). Add links in both places:

- `notebooks/README.md` — a row in the published notebooks table, keeping it alphabetical:
  `| Title | [View](https://koysor.github.io/quant-finance/$0.html) | [Edit code](https://koysor.github.io/quant-finance/$0-edit.html) |`
- `README.md` — a bullet in the "Interactive Marimo Notebooks" list:
  `* Title ([view](https://koysor.github.io/quant-finance/$0.html) · [edit code](https://koysor.github.io/quant-finance/$0-edit.html))`

## Verification

Run each of these and fix any failures before finishing:

```bash
uv run marimo check notebooks/$0.py
uv run pytest tests/test_notebooks.py
uv run ruff check notebooks/$0.py
uv run black notebooks/$0.py
```

Optionally open it with `uv run marimo edit notebooks/$0.py` to check the widgets and plots look right.
