"""Smoke tests: every Streamlit page runs without raising.

Each page is run headless with Streamlit's AppTest, and each button on it is
clicked, so code that only runs after a click (simulations, plots) is
covered too. This catches import errors, typos and library API changes in
pages, which the unit tests do not exercise.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parent.parent
PAGES = sorted(ROOT.glob("app_*/pages/*.py")) + sorted(ROOT.glob("app_*/*.py"))


def test_pages_were_found():
    """Guards the test below against passing because the glob found nothing."""
    assert len(PAGES) >= 4


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(ROOT)))
def test_page_runs(page, monkeypatch):
    # Entry scripts load images by paths relative to the repository root
    monkeypatch.chdir(ROOT)
    app = AppTest.from_file(str(page), default_timeout=120).run()
    assert not app.exception, [e.value for e in app.exception]

    for index in range(len(app.button)):
        app.button[index].click().run()
        assert not app.exception, [e.value for e in app.exception]
