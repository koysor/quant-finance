---
name: launch-app
description: Launch one of the four Streamlit applications locally
disable-model-invocation: true
argument-hint: [quant-finance|options|fixed-income|portfolio]
allowed-tools: Bash(source:*), Bash(uv run streamlit:*)
---

Launch a Streamlit app from the quantitative finance project.

**App to launch:** $ARGUMENTS

Run the matching command in the background:

- **quant-finance**: `source .venv/bin/activate && uv run streamlit run app_quant_finance/quantitative_finance.py`
- **options**: `source .venv/bin/activate && uv run streamlit run app_options/options.py`
- **fixed-income**: `source .venv/bin/activate && uv run streamlit run app_fixed_income/fixed_income.py`
- **portfolio**: `source .venv/bin/activate && uv run streamlit run app_portfolio_management/portfolio_management.py`

If no argument is provided, ask the user which app to launch.
