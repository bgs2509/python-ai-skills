"""Tests for lib/stagnation.py."""
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))
import stagnation  # noqa: E402


def _write(path: Path, fps: list[tuple[str, str]]):
    path.write_text(json.dumps({
        "findings": [{"fingerprint": fp, "severity": sev} for fp, sev in fps],
    }))


def test_no_prev_returns_false(tmp_path):
    cur = tmp_path / "r1.json"
    _write(cur, [("aaa", "critical")])
    out = stagnation.detect(cur, None)
    assert out["stagnation"] is False
    assert out["prev_critical"] == 0


def test_no_overlap_no_stagnation(tmp_path):
    cur, prev = tmp_path / "r2.json", tmp_path / "r1.json"
    _write(prev, [("aaa", "critical"), ("bbb", "critical")])
    _write(cur, [("ccc", "critical")])
    out = stagnation.detect(cur, prev)
    assert out["stagnation"] is False
    assert out["repeated"] == 0


def test_full_overlap_triggers_stagnation(tmp_path):
    cur, prev = tmp_path / "r2.json", tmp_path / "r1.json"
    _write(prev, [("aaa", "critical"), ("bbb", "critical")])
    _write(cur, [("aaa", "critical"), ("bbb", "critical")])
    out = stagnation.detect(cur, prev)
    assert out["stagnation"] is True
    assert out["repeated"] == 2


def test_threshold_boundary(tmp_path):
    cur, prev = tmp_path / "r2.json", tmp_path / "r1.json"
    _write(prev, [("a", "critical"), ("b", "critical"), ("c", "critical"), ("d", "critical")])
    _write(cur, [("a", "critical"), ("b", "critical")])  # 2/4 = 0.5
    assert stagnation.detect(cur, prev, threshold=0.5)["stagnation"] is True
    assert stagnation.detect(cur, prev, threshold=0.6)["stagnation"] is False


def test_only_critical_severity_counts(tmp_path):
    cur, prev = tmp_path / "r2.json", tmp_path / "r1.json"
    _write(prev, [("aaa", "medium"), ("bbb", "medium")])
    _write(cur, [("aaa", "medium"), ("bbb", "medium")])
    out = stagnation.detect(cur, prev)
    assert out["stagnation"] is False  # no critical → no stagnation
    assert out["prev_critical"] == 0
