#!/bin/bash

echo "Starting the Streamlit app for Fixed Income..."

# Resolve paths relative to this script so it works from any directory
cd "$(dirname "$(readlink -f "$0")")" || exit 1

# uv lives in ~/.local/bin, which is missing from PATH in non-login shells
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

VENV_DIR=".venv"
APP_SCRIPT="app_fixed_income/fixed_income.py"

source "$VENV_DIR/bin/activate"

# Run the Streamlit app
uv run streamlit run "$APP_SCRIPT"
