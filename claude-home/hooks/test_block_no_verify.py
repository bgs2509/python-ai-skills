"""Regression suite for the block-no-verify PreToolUse hook.

The hook is the enforcement half of CLAUDE.md -> "Pre-commit Policy": it must
refuse commit-hook bypasses and must never block ordinary git work. Three
bypasses have been found by hand so far (`git -C <path> commit`, short `-n`,
and a second command after `&&`); each one is pinned here so the next edit to
the parser cannot silently reopen it.

Hook contract: exit 2 = blocked, exit 0 = allowed.

Run: pytest claude-home/hooks/test_block_no_verify.py
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).parent / "block-no-verify.sh"


def run_hook(command: str) -> int:
    """Feed one Bash command to the hook the way Claude Code does."""
    payload = json.dumps({"tool_input": {"command": command}})
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.returncode


BLOCKED = [
    # Direct bypass flags.
    "git commit --no-verify -m x",
    "git commit -n -m x",
    "git commit --no-gpg-sign -m x",
    "git merge --no-verify feature",
    "git rebase --no-verify main",
    "git cherry-pick --no-verify abc123",
    # Global git options before the subcommand (fixed in be4efe4).
    "git -C /tmp/repo commit --no-verify -m x",
    "git -c user.name=x commit --no-verify -m x",
    # A second command on the same line (the `tokens.index` bypass).
    "git add -A && git commit --no-verify -m x",
    "git status && git commit --no-verify -m x",
    "cd /tmp && git add . && git commit --no-verify -m x",
    "git add -A; git commit --no-verify -m x",
    "cd /tmp; git commit --no-verify -m x",
    "git add -A || git commit -n -m x",
    # Bypass flag placed after the message.
    "git commit -m 'msg' --no-verify",
    # Env-var bypasses named in the Pre-commit Policy.
    "SKIP=ruff git commit -m x",
    "PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m x",
]

ALLOWED = [
    # Ordinary commits, including the chained form that must not false-positive.
    "git commit -m 'ok'",
    "git add -A && git commit -m 'ok'",
    "git add -A && git commit -m 'ok' && git status",
    "git status",
    "git log --oneline -5",
    "git push origin main",
    # `-n` means something else for these subcommands.
    "git merge -n feature",
    "git cherry-pick -n abc123",
    # The flag appears only inside the commit message, not as a token.
    "git commit -m 'fix --no-verify bypass in hook'",
    "git commit --message='block --no-verify properly'",
    # Not a git command at all.
    "echo 'git commit --no-verify'",
    "grep -rn 'no-verify' docs/",
    # No command at all / unparseable input must not crash the hook.
    "",
    "git commit -m 'unbalanced quote",
]


@pytest.mark.parametrize("command", BLOCKED)
def test_bypass_is_blocked(command):
    assert run_hook(command) == 2, f"hook allowed a bypass: {command!r}"


@pytest.mark.parametrize("command", ALLOWED)
def test_ordinary_command_is_allowed(command):
    assert run_hook(command) == 0, f"hook blocked legitimate work: {command!r}"
