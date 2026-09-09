"""Regression suite for the big-read-nudge PreToolUse hook.

The hook is the soft half of the token-saving policy: when Read targets a file
longer than a threshold, it injects a reminder (via
hookSpecificOutput.additionalContext) nudging the model to delegate whole-file
comprehension to a sonnet subagent, or to use grep / a targeted offset read. It
never blocks — Read always runs — and it must stay silent for small files and
for reads that are already targeted (offset or limit set).

Hook contract: always exit 0. stdout carries the additionalContext JSON only
when nudging; empty stdout otherwise.

Run: pytest claude-home/hooks/test_big_read_nudge.py
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

HOOK = Path(__file__).parent / "big-read-nudge.sh"
DEFAULT_THRESHOLD = 400


def make_file(lines: int) -> str:
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(f"line {i}" for i in range(lines)))
    return path


def run_hook(tool_input: dict, env_extra: dict | None = None):
    """Feed one Read tool_input to the hook the way Claude Code does."""
    payload = json.dumps(
        {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": tool_input}
    )
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=15,
        env={**os.environ, **(env_extra or {})},
    )
    return result


def nudges(result) -> bool:
    """True if the hook injected a PreToolUse additionalContext reminder."""
    out = result.stdout.strip()
    if not out:
        return False
    data = json.loads(out)
    ctx = data["hookSpecificOutput"]["additionalContext"]
    assert data["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    return "sonnet" in ctx.lower()


def test_large_plain_read_nudges():
    path = make_file(DEFAULT_THRESHOLD + 50)
    try:
        result = run_hook({"file_path": path})
        assert result.returncode == 0
        assert nudges(result), "expected a nudge for a large plain read"
    finally:
        os.unlink(path)


def test_small_read_is_silent():
    path = make_file(DEFAULT_THRESHOLD - 50)
    try:
        result = run_hook({"file_path": path})
        assert result.returncode == 0
        assert not result.stdout.strip(), "small file must not nudge"
    finally:
        os.unlink(path)


def test_targeted_read_with_offset_is_silent():
    path = make_file(DEFAULT_THRESHOLD + 50)
    try:
        result = run_hook({"file_path": path, "offset": 100})
        assert result.returncode == 0
        assert not result.stdout.strip(), "offset read is already targeted"
    finally:
        os.unlink(path)


def test_targeted_read_with_limit_is_silent():
    path = make_file(DEFAULT_THRESHOLD + 50)
    try:
        result = run_hook({"file_path": path, "limit": 50})
        assert result.returncode == 0
        assert not result.stdout.strip(), "limit read is already targeted"
    finally:
        os.unlink(path)


def test_threshold_overridable_via_env():
    path = make_file(250)  # below default 400, above custom 200
    try:
        result = run_hook({"file_path": path}, env_extra={"BIG_READ_NUDGE_LINES": "200"})
        assert result.returncode == 0
        assert nudges(result), "custom lower threshold must trigger a nudge"
    finally:
        os.unlink(path)


def test_missing_file_is_silent():
    result = run_hook({"file_path": "/nonexistent/path/to/file.py"})
    assert result.returncode == 0
    assert not result.stdout.strip()


def test_missing_file_path_is_silent():
    result = run_hook({})
    assert result.returncode == 0
    assert not result.stdout.strip()


def test_malformed_stdin_does_not_crash():
    result = subprocess.run(
        ["bash", str(HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert not result.stdout.strip()
