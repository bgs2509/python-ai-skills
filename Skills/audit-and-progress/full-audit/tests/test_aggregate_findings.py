"""Tests for the per-run findings aggregator."""
import json
from pathlib import Path

from aggregate_findings import aggregate


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)


def test_aggregate_combines_ruff_and_mypy(tmp_path: Path, golden_dir: Path):
    excerpts = tmp_path / "excerpts"
    _write(excerpts / "01-ruff-check.txt", (golden_dir / "ruff_concise.txt").read_text())
    _write(excerpts / "03-mypy.txt", (golden_dir / "mypy.txt").read_text())
    out = tmp_path / "findings.jsonl"

    n = aggregate(excerpts, out, ai_report_path=None, self_check_sidecars=[])

    assert n == 5   # 3 ruff + 2 mypy
    lines = out.read_text().splitlines()
    assert len(lines) == 5
    rec = json.loads(lines[0])
    assert "fingerprint" in rec
    assert "fingerprint_loose" in rec
    assert len(rec["fingerprint"]) == 40
    assert rec["check_id"] in {"01-ruff-check", "03-mypy"}
