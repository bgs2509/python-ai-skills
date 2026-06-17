"""Tests for lib/lock.py."""
import json
import os
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib" / "lock.py"


def _run(args, cwd):
    return subprocess.run([sys.executable, str(LIB), *args], capture_output=True, text=True, cwd=cwd)


def test_acquire_creates_lockfile(tmp_path):
    r = _run(["acquire"], tmp_path)
    assert r.returncode == 0
    assert (tmp_path / "docs/audit-loop/.lock").exists()


def test_acquire_blocks_when_alive_pid(tmp_path):
    lock_path = tmp_path / "docs/audit-loop/.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps({"pid": os.getpid(), "ts": "now"}))  # current pid is alive
    r = _run(["acquire"], tmp_path)
    assert r.returncode == 2
    assert "already running" in r.stderr


def test_acquire_overwrites_stale_pid(tmp_path):
    lock_path = tmp_path / "docs/audit-loop/.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps({"pid": 999999, "ts": "old"}))  # very unlikely PID
    r = _run(["acquire"], tmp_path)
    assert r.returncode == 0
    data = json.loads(lock_path.read_text())
    assert data["pid"] != 999999


def test_release_removes_lockfile(tmp_path):
    _run(["acquire"], tmp_path)
    r = _run(["release"], tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / "docs/audit-loop/.lock").exists()


def test_release_idempotent(tmp_path):
    r = _run(["release"], tmp_path)
    assert r.returncode == 0


def test_bad_args_exits_2(tmp_path):
    r = _run(["bogus"], tmp_path)
    assert r.returncode == 2
