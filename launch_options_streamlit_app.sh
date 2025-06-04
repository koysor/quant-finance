#!/bin/bash

echo "Starting the Streamlit app for Options..."

VENV_DIR=".venv"
APP_SCRIPT="app_options/options.py"

source "$VENV_DIR/bin/activate"

# Run the Streamlit app
streamlit run "$APP_SCRIPT"