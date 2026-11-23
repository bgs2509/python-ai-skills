"""Tests for trend detectors over audit history."""
from check_trends import find_cross_breaking, find_oscillating, find_sticky


def _h(commit: str, fp: str, **extra) -> dict:
    """Build a synthetic history record with sensible defaults."""
    return {
        "commit": commit, "run_id": commit, "date": "2026-05-01",
        "check_id": "03-mypy", "file": "src/foo.py", "line": 42,
        "line_bucket": 8, "severity": "middle", "rule_id": "x",
        "message_raw": "m", "message_canonical": "m",
        "fingerprint": fp, "fingerprint_loose": fp + "L",
        **extra,
    }


# ---- Sticky ----------------------------------------------------------------

def test_sticky_requires_min_consecutive_runs():
    history = [_h("c1", "FP1"), _h("c2", "FP1"), _h("c3", "FP1")]
    sticky = find_sticky(history, min_consecutive=3)
    assert len(sticky) == 1
    assert sticky[0]["fingerprint"] == "FP1"
    assert sticky[0]["consecutive_runs"] == 3
    assert sticky[0]["first_seen_commit"] == "c1"


def test_sticky_ignores_finding_with_gap():
    # FP1 appears in c1, c2, then replaced by FP2 in c3 → not sticky in window=3
    history = [_h("c1", "FP1"), _h("c2", "FP1"), _h("c3", "FP2")]
    sticky = find_sticky(history, min_consecutive=3)
    assert sticky == []


# ---- Oscillating -----------------------------------------------------------

def test_oscillating_detects_on_off_on():
    # window: c1 c2 c3 c4 c5; FP1: present absent present absent present (pattern X.X.X)
    # FP_STUB keeps every run "non-empty" so _runs_in_order sees all 5.
    h = [
        _h("c1", "FP1"), _h("c1", "FP_STUB"),
        _h("c2", "FP_STUB"),
        _h("c3", "FP1"), _h("c3", "FP_STUB"),
        _h("c4", "FP_STUB"),
        _h("c5", "FP1"), _h("c5", "FP_STUB"),
    ]
    osc = find_oscillating(h, window=5, min_cycles=2)
    fps = [o["fingerprint"] for o in osc]
    assert "FP1" in fps


def test_oscillating_ignores_steady_finding():
    h = [_h(c, "FP1") for c in ("c1", "c2", "c3", "c4", "c5")]
    assert find_oscillating(h, window=5, min_cycles=2) == []


# ---- Cross-breaking --------------------------------------------------------

def test_cross_breaking_pair_repeats():
    def f(commit: str, fp: str, file_: str) -> dict:
        return _h(commit, fp, file=file_)

    h = [
        # c1: A present, B absent
        f("c1", "A", "src/processor/m2.py"),
        # c2: A removed, B appeared (fix-A introduces B)
        f("c2", "B", "src/processor/m2.py"),
        # c3: B removed, A reappeared (fix-B brings A back)
        f("c3", "A", "src/processor/m2.py"),
        # c4: A removed, B reappeared (cycle repeats)
        f("c4", "B", "src/processor/m2.py"),
    ]
    pairs = find_cross_breaking(h, min_repeats=2)
    assert len(pairs) == 1
    p = pairs[0]
    assert set([p["fingerprint_a"], p["fingerprint_b"]]) == {"A", "B"}
    assert p["repeats"] >= 2
    assert p["module"] == "processor"


def test_cross_breaking_ignores_single_swap():
    # A→B happens once at c1→c2, then B persists. Not a pair (only 1 boundary).
    h = [
        _h("c1", "A", file="src/processor/m2.py"),
        _h("c2", "B", file="src/processor/m2.py"),
    ]
    assert find_cross_breaking(h, min_repeats=2) == []


def test_cross_breaking_ignores_cross_module_swap():
    # A disappears in processor module, B appears in ingestor module → different
    # modules, must NOT pair.
    h = [
        _h("c1", "A", file="src/processor/m2.py"),
        _h("c2", "B", file="src/ingestor/parse.py"),
    ]
    assert find_cross_breaking(h, min_repeats=2) == []


def _sentinel(commit: str) -> dict:
    return {
        "commit": commit, "run_id": commit, "date": "2026-05-22",
        "_sentinel": True,
    }


def test_sentinel_runs_count_but_do_not_introduce_findings():
    """A run with only a sentinel entry contributes to run-count
    but contains no fingerprints to match."""
    history = [
        _sentinel("c1"),
        _sentinel("c2"),
        _h("c3", "FP1"),
        _h("c3", "FP_OTHER"),
    ]
    # sticky needs 3 consecutive runs with FP1 in all of them — sentinel
    # runs have empty fingerprint set, so FP1 is NOT sticky here.
    assert find_sticky(history, min_consecutive=3) == []


def test_sentinel_run_makes_total_runs_advance():
    """Verifies _runs_in_order counts sentinel runs — proving trend rendering
    will fire once enough total runs accumulate, even if findings are zero."""
    from check_trends import _runs_in_order

    history = [_sentinel("c1"), _sentinel("c2"), _sentinel("c3")]
    assert _runs_in_order(history) == ["c1", "c2", "c3"]
