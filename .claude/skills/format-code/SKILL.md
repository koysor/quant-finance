---
name: format-code
description: Format code with black and lint with ruff
disable-model-invocation: true
allowed-tools: Bash(black:*), Bash(ruff:*)
---

Format and validate code in the quantitative finance project.

1. Format with black: `black .`
2. Lint with ruff: `ruff check .`
3. Report any violations with file paths and line numbers
4. If ruff finds auto-fixable issues, ask the user whether to run `ruff check --fix .`
