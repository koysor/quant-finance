#!/bin/bash

echo "Starting the Streamlit app for Portfolio Management..."

VENV_DIR=".venv"
APP_SCRIPT="app_portfolio_management/portfolio_management.py"

source "$VENV_DIR/bin/activate"

# Run the Streamlit app
uv run streamlit run "$APP_SCRIPT"
