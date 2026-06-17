"""Tests for the trends section renderer."""
from render_trends import render_trends_section


def test_render_includes_three_subsections():
    sticky = [{
        "fingerprint": "a" * 40, "check_id": "03-mypy", "file": "src/foo.py",
        "line": 42, "severity": "middle", "message_raw": "m",
        "consecutive_runs": 3, "first_seen_commit": "c1", "last_seen_commit": "c3",
    }]
    osc = [{
        "fingerprint": "b" * 40, "check_id": "01-ruff-check", "file": "src/bar.py",
        "line": 10, "severity": "middle", "message_raw": "m", "cycles": 2,
        "pattern": "X.X.X", "runs_window": ["c1", "c2", "c3", "c4", "c5"],
    }]
    cb = [{
        "module": "processor", "fingerprint_a": "A", "fingerprint_b": "B",
        "repeats": 2, "boundaries": [("c1", "c2"), ("c3", "c4")],
    }]
    md = render_trends_section(sticky, osc, cb, total_runs=5)
    assert "## Trends" in md
    assert "### Sticky" in md
    assert "### Oscillating" in md
    assert "### Cross-breaking pairs" in md
    assert "src/foo.py:42" in md
    assert "src/bar.py:10" in md
    assert "processor" in md


def test_render_returns_empty_when_history_too_short():
    md = render_trends_section([], [], [], total_runs=2)
    assert md == ""


def test_render_handles_empty_categories_with_history():
    md = render_trends_section([], [], [], total_runs=3)
    assert "## Trends" in md
    assert "### Sticky" in md
    assert "- none" in md   # each empty subsection renders "- none"
