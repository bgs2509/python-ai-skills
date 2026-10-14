"""Backwards-compat regression test for self-check scripts.

Runs each self-check script as a subprocess in a clean temp dir (no docs/, no src/,
no pyproject.toml, not a git repo) and asserts the script exits cleanly with the
expected 'skipping / not applicable' message. Purpose: catch any drift introduced
by Task 6b when the same `--json-out` integration is applied to the other 4 scripts.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parent.parent / "lib"

# (script_filename, expected substring in stdout OR stderr)
# We accept either stream because check_secret_files prints its skip message to stderr.
CASES = [
    ("check_ssot.py",         "docs/ absent — skipping SSoT drift checks"),
    ("check_anchors.py",      "no source dirs given — skipping"),
    ("check_contracts.py",    "no source dirs given — skipping"),
    ("check_pins.py",         "pyproject.toml absent"),
    ("check_secret_files.py", "not a git repo — skipped"),
]


@pytest.mark.parametrize("script,expected_msg", CASES)
def test_self_check_clean_dir_is_no_op(
    script: str, expected_msg: str, tmp_path: Path
) -> None:
    """In a fresh empty dir each self-check exits 0 with a 'skipping' line."""
    result = subprocess.run(
        [sys.executable, str(LIB / script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, (
        f"{script} exited {result.returncode} in clean dir; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert expected_msg in combined, (
        f"{script} did not print expected skip message {expected_msg!r}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


RUN_SH = LIB / "run.sh"


def _run(script: str, cwd: Path, *dirs: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LIB / script), *dirs],
        cwd=cwd, capture_output=True, text=True,
    )


def _app(tmp_path: Path, body: str) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "mod.py").write_text(body)


def test_contracts_checks_given_non_src_dir(tmp_path: Path) -> None:
    _app(tmp_path, "x = 1\n")
    result = _run("check_contracts.py", tmp_path, "app")
    assert result.returncode == 1
    assert "app/mod.py" in result.stdout


def test_anchors_checks_given_non_src_dir(tmp_path: Path) -> None:
    _app(tmp_path, "# START_BLOCK_A\n")
    result = _run("check_anchors.py", tmp_path, "app")
    assert result.returncode == 1
    assert "unpaired" in result.stdout


def test_ssot_compares_graph_with_given_dirs(tmp_path: Path) -> None:
    _app(tmp_path, "x = 1\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "knowledge-graph.xml").write_text(
        '<g><m FILE="app/mod.py"/><m FILE="app/gone.py"/></g>'
    )
    result = _run("check_ssot.py", tmp_path, "app")
    assert result.returncode == 1
    assert "app/gone.py" in result.stdout


@pytest.mark.parametrize(
    "script", ["check_ssot.py", "check_anchors.py", "check_contracts.py"]
)
def test_run_sh_passes_derived_dirs(script: str) -> None:
    text = RUN_SH.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if script in ln)
    assert '"${METRIC_DIRS[@]}"' in line


def test_run_sh_skips_anchor_and_contract_checks_without_dirs() -> None:
    text = RUN_SH.read_text(encoding="utf-8")
    assert 'skip "11-block-anchors" "block anchors paired" "$NO_SRC_REASON"' in text
    assert 'skip "12-contracts" "MODULE_CONTRACT presence" "$NO_SRC_REASON"' in text
