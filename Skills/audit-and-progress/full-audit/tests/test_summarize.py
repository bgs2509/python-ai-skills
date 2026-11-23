"""Final verdict line of summarize.py (bd python-ai-skills-aw0.2)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "lib" / "summarize.py"


def _summarize(tmp_path: Path, rows: list[dict]) -> subprocess.CompletedProcess[str]:
    results = tmp_path / "results.jsonl"
    results.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(results)], capture_output=True, text=True
    )


def _row(check_id: str, status: str) -> dict:
    return {"id": check_id, "name": check_id, "status": status, "exit": 0, "metric": "-"}


def test_skipped_required_check_is_named_not_reported_as_pass(tmp_path: Path) -> None:
    result = _summarize(
        tmp_path,
        [_row("01-ruff-check", "PASS"), _row("06-pytest-unit", "SKIPPED"),
         _row("12-contracts", "SKIPPED")],
    )
    assert result.returncode == 0
    assert "all required checks PASS" not in result.stdout
    assert "no required failures; 2 required check(s) SKIPPED:\n    06-pytest-unit, 12-contracts" in result.stdout


def test_skipped_optional_check_keeps_all_pass_line(tmp_path: Path) -> None:
    result = _summarize(
        tmp_path, [_row("01-ruff-check", "PASS"), _row("14-radon-cc", "SKIPPED")]
    )
    assert result.returncode == 0
    assert "Exit 0 — all required checks PASS" in result.stdout


def test_required_failure_still_exits_1(tmp_path: Path) -> None:
    result = _summarize(
        tmp_path, [_row("03-mypy", "FAIL"), _row("06-pytest-unit", "SKIPPED")]
    )
    assert result.returncode == 1
    assert "Exit 1 — 1 required failure(s)" in result.stdout
