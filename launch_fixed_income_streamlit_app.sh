#!/bin/bash

echo "Starting the Streamlit app for Fixed Income..."

VENV_DIR=".venv"
APP_SCRIPT="app_fixed_income/fixed_income.py"

source "$VENV_DIR/bin/activate"

# Run the Streamlit app
uv run streamlit run "$APP_SCRIPT"
