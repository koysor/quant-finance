# Projects

Each project answers one specific question and can be reproduced from a single command. This directory holds the question, configuration, results and write-up. Reusable logic belongs in the library.

## Rules

1. **Logic lives in the library.** Put models and algorithms in `src/quant_finance/` and tests in `tests/`. A project's `run.py` only wires them together.
2. **Streamlit is optional.** An app page can present a project, but it must import its calculations from `quant_finance`.
3. **Results must be reproducible.** Fix random seeds, keep parameters in a config file and commit the outputs the write-up relies on to `results/`.
4. **State the limitations.** Name the data source and its known biases, such as survivorship bias in yfinance data.

## Layout

```text
projects/<project_name>/
├── README.md     # Write-up, using the sections below
├── run.py        # Single entry point: uv run python projects/<project_name>/run.py
├── config.toml   # Parameters and random seeds
└── results/      # Committed outputs used in the write-up
```

## Required README sections

| Section | Content |
|---------|---------|
| **Question** | What the project tries to answer, in one or two sentences |
| **Method** | The model or algorithm, with the key formulae and the design choices made |
| **Results** | Headline numbers and charts, compared with a baseline or benchmark |
| **Validation** | How the results were checked: known values, invariants or independent implementations |
| **Limitations** | Assumptions, data issues and what would change the conclusion |
| **How to run** | The exact commands, and the expected runtime |
