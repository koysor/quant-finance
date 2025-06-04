#!/bin/bash

echo "Starting the Streamlit app for Quant Finance..."

VENV_DIR=".venv"
APP_SCRIPT="app_quant_finance/quantitative_finance.py"

source "$VENV_DIR/bin/activate"

# Run the Streamlit app
streamlit run "$APP_SCRIPT"