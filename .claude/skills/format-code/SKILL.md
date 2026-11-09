---
name: format-code
description: Format code and lint it with ruff
disable-model-invocation: true
allowed-tools: Bash(uv run ruff:*)
---

Format and validate code in the quantitative finance project.

1. Format with ruff: `uv run ruff format .`
2. Lint with ruff: `uv run ruff check .`
3. Report any violations with file paths and line numbers
4. If ruff finds auto-fixable issues, ask the user whether to run `uv run ruff check --fix .`
