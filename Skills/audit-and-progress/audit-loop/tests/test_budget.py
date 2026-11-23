"""Tests for lib/budget.py."""
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))
import budget  # noqa: E402


def _state(rounds: list[list[tuple[str, str]]]) -> dict:
    """rounds = [[(fp, src), ...], ...] where src ∈ auto_applied|asked|still_open."""
    return {"rounds": [
        {src: [{"fingerprint": fp} for f, src_ in items if src_ == src]
         for src in ("auto_applied", "asked", "still_open", "deferred")
         for f, _ in [(None, None)]}  # init keys
        | {src: [{"fingerprint": f} for f, s in items if s == src]
           for src in ("auto_applied", "asked", "still_open", "deferred")}
        for items in rounds
    ]}


def test_zero_appearances():
    assert budget.appearances("aaa", {"rounds": []}) == 0


def test_counts_one_per_round():
    state = {"rounds": [
        {"auto_applied": [{"fingerprint": "aaa"}], "asked": [], "still_open": []},
        {"auto_applied": [], "asked": [{"fingerprint": "aaa"}], "still_open": []},
    ]}
    assert budget.appearances("aaa", state) == 2


def test_dedupes_within_round():
    state = {"rounds": [
        {"auto_applied": [{"fingerprint": "aaa"}],
         "asked": [{"fingerprint": "aaa"}],
         "still_open": [{"fingerprint": "aaa"}]},
    ]}
    assert budget.appearances("aaa", state) == 1


def test_over_budget_threshold():
    state = {"rounds": [
        {"auto_applied": [{"fingerprint": "x"}], "asked": [], "still_open": []},
        {"auto_applied": [], "asked": [], "still_open": [{"fingerprint": "x"}]},
    ]}
    assert budget.over_budget("x", state, limit=2) is True
    assert budget.over_budget("x", state, limit=3) is False


def test_ignores_other_fingerprints():
    state = {"rounds": [
        {"auto_applied": [{"fingerprint": "yyy"}], "asked": [], "still_open": []},
    ]}
    assert budget.appearances("xxx", state) == 0
