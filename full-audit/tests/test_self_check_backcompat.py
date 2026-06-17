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
    ("check_anchors.py",      "src/ absent — skipping"),
    ("check_contracts.py",    "src/ absent — skipping"),
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
