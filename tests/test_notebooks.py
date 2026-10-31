"""Tests that notebooks published to GitHub Pages can run in the browser."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

NOTEBOOKS_DIR = Path(__file__).parent.parent / "notebooks"
PUBLISHED_NOTEBOOKS = sorted(NOTEBOOKS_DIR.glob("*.py"))
BROWSER_SAFE_PACKAGES = {"marimo", "numpy", "pandas", "matplotlib"}


def _imported_packages(path: Path) -> set[str]:
    """Return the top-level packages imported anywhere in a Python file."""
    packages = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            packages.add(node.module.split(".")[0])
    return packages


def test_published_notebooks_exist():
    """Guards the tests below against passing because the glob found nothing."""
    assert PUBLISHED_NOTEBOOKS


@pytest.mark.parametrize("notebook", PUBLISHED_NOTEBOOKS, ids=lambda path: path.stem)
class TestPublishedNotebook:
    """Checks for each notebook exported to GitHub Pages."""

    def test_imports_only_browser_safe_packages(self, notebook):
        unsafe = _imported_packages(notebook) - BROWSER_SAFE_PACKAGES
        assert not unsafe, f"Move {notebook.name} to notebooks/local/: imports {unsafe}"

    def test_runs_as_a_script(self, notebook):
        result = subprocess.run(
            [sys.executable, str(notebook)],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
        assert result.returncode == 0, result.stderr
