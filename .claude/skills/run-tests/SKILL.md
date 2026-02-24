---
name: run-tests
description: Run the pytest test suite
disable-model-invocation: true
allowed-tools: Bash(uv run pytest:*)
---

Run the test suite for the quantitative finance project.

1. Run all tests: `uv run pytest tests/ -v --tb=short`
2. Report failures with file path and line number
3. If all tests pass, confirm the total count
