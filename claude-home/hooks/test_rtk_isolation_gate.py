"""Tests for rtk-isolation-gate.sh — keeps RTK away from git inside linked worktrees.

A background session isolated in a worktree has its git commands vetted by the
harness, which refuses `rtk git ...` ("runs rtk with a git command among its
operands"). Observed 2026-10-13: every rewritten git call was refused and the
model fell back to /usr/bin/git. The gate must skip the wrapped hook for git
commands run from a linked worktree, and delegate unchanged everywhere else.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "rtk-isolation-gate.sh"


@pytest.fixture
def repo(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args, cwd=main):
        subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")
    linked = tmp_path / "linked"
    git("worktree", "add", "-q", "-b", "work", str(linked))
    return main, linked


@pytest.fixture
def probe(tmp_path):
    """A stand-in for the wrapped hook: echoes a marker and the stdin it received."""
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    gate = hooks / "rtk-isolation-gate.sh"
    gate.write_bytes(HOOK.read_bytes())
    gate.chmod(0o755)
    target = hooks / "probe.sh"
    target.write_text('#!/usr/bin/env bash\necho "DELEGATED:$(cat)"\n')
    target.chmod(0o755)
    return gate


def run(gate, command, cwd):
    payload = {"cwd": str(cwd), "tool_input": {"command": command}}
    return subprocess.run(
        ["bash", str(gate), "probe.sh"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    "command",
    ["git status", "git -C . log --oneline -3", "cd sub && git diff", "ls; git branch"],
)
def test_git_in_linked_worktree_skips_rtk(repo, probe, command):
    _, linked = repo
    result = run(probe, command, linked)
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("command", ["git status", "ls -la"])
def test_main_clone_delegates(repo, probe, command):
    main, _ = repo
    result = run(probe, command, main)
    assert result.stdout.startswith("DELEGATED:")
    assert json.loads(result.stdout[len("DELEGATED:"):])["tool_input"]["command"] == command


def test_non_git_command_in_linked_worktree_delegates(repo, probe):
    _, linked = repo
    result = run(probe, "ls -la", linked)
    assert result.stdout.startswith("DELEGATED:")


@pytest.mark.parametrize("command", ["cat .gitignore", "echo legit", "gitleaks protect"])
def test_git_substring_is_not_git(repo, probe, command):
    _, linked = repo
    assert run(probe, command, linked).stdout.startswith("DELEGATED:")


def test_outside_git_delegates(tmp_path, probe):
    assert run(probe, "git status", tmp_path).stdout.startswith("DELEGATED:")
