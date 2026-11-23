"""Tests for the persistent audit history store."""
import json
from pathlib import Path

from history_store import append_run, read_history


def _findings(tmp_path: Path, items: list[dict]) -> Path:
    p = tmp_path / "findings.jsonl"
    p.write_text("\n".join(json.dumps(i) for i in items))
    return p


def test_append_run_writes_findings_with_commit_metadata(tmp_path: Path, tmp_history: Path):
    fp = _findings(tmp_path, [
        {"check_id": "03-mypy", "file": "src/foo.py", "line": 42,
         "line_bucket": 8, "severity": "middle", "rule_id": "x",
         "message_raw": "msg", "message_canonical": "msg",
         "fingerprint": "a"*40, "fingerprint_loose": "b"*40},
    ])
    append_run(tmp_history, fp, commit="abc1234", run_id="2026-05-22T10:00:00Z")

    history = read_history(tmp_history)
    assert len(history) == 1
    rec = history[0]
    assert rec["commit"] == "abc1234"
    assert rec["fingerprint"] == "a"*40
    assert rec["check_id"] == "03-mypy"


def test_append_run_is_append_only(tmp_path: Path, tmp_history: Path):
    fp = _findings(tmp_path, [
        {"check_id": "03-mypy", "file": "src/foo.py", "line": 42,
         "line_bucket": 8, "severity": "middle", "rule_id": "x",
         "message_raw": "m1", "message_canonical": "m1",
         "fingerprint": "a"*40, "fingerprint_loose": "b"*40},
    ])
    append_run(tmp_history, fp, commit="c1", run_id="r1")
    append_run(tmp_history, fp, commit="c2", run_id="r2")

    history = read_history(tmp_history)
    assert len(history) == 2
    assert [r["commit"] for r in history] == ["c1", "c2"]


def test_append_run_writes_sentinel_when_zero_findings(tmp_path, tmp_history):
    """When findings.jsonl is empty, a sentinel row is appended so the run is
    countable in history even though no findings exist."""
    empty_findings = tmp_path / "findings.jsonl"
    empty_findings.write_text("")   # explicit empty

    n = append_run(tmp_history, empty_findings, commit="c1", run_id="r1")

    assert n == 0   # function return reflects real findings count
    history = read_history(tmp_history)
    assert len(history) == 1
    rec = history[0]
    assert rec.get("_sentinel") is True
    assert rec["run_id"] == "r1"
    assert rec["commit"] == "c1"
