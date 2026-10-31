---
name: new-page
description: Generate a new Streamlit page following project conventions
disable-model-invocation: true
argument-hint: [app-name] [page-name]
---

Create a new Streamlit page following the quantitative finance project conventions.

**App:** $0 (one of: quant_finance, options, fixed_income, portfolio_management)
**Page name:** $1 (snake_case filename without .py extension)

The generated page MUST follow these conventions:

1. **Imports** — `import streamlit as st` plus any needed libraries (numpy, matplotlib, scipy)
2. **Page config** — `st.set_page_config(page_title="...", page_icon="...", layout="wide")` with the correct icon:
   - `app_quant_finance/` — `📊`
   - `app_options/` — `📈`
   - `app_fixed_income/` — `🏦`
   - `app_portfolio_management/` — `💼`
3. **Header** — `st.header("Page Title")`
4. **Educational content** — introductory `st.write()` explaining the concept
5. **Calculations** — import from `quant_finance` (add to `src/quant_finance/` with tests in `tests/` if missing); do not define models in the page
6. **Mathematical formulation** — LaTeX via `st.latex()` with corresponding `st.code(latex_code, language="latex")`
7. **Interactive example** — sliders/inputs with a matplotlib visualisation
8. **British English spelling** throughout (e.g. optimise, modelling, colour)

Create the file at: `app_$0/pages/$1.py`
