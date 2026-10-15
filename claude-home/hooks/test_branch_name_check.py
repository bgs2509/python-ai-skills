"""Regression suite for the branch-name-check PreToolUse hook.

The hook is the enforcement half of the N-BRANCH rule (claude-home/CLAUDE.md ->
"Naming"): it denies Bash git commands and EnterWorktree calls that create a branch
whose name has no `branch` segment, and must never block ordinary git work.

Hook contract: exit 2 = denied, exit 0 = allowed.

Run: pytest claude-home/hooks/test_branch_name_check.py
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "branch-name-check.sh"
# No GIT_* variable may leak in: pre-commit runs this suite with GIT_INDEX_FILE (and
# possibly GIT_DIR) set, which would point `git init` and `git rev-parse` at the real repository.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def make_repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True, env=ENV)
    return path


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return make_repo(tmp_path_factory.mktemp("repo"))


@pytest.fixture
def home(tmp_path):
    """Fake HOME: the block journal (~/.claude/hook-stats/blocks.jsonl) never touches the real one."""
    path = tmp_path / "home"
    path.mkdir()
    return path


def run_hook(stdin, home):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=stdin if isinstance(stdin, str) else json.dumps(stdin),
        capture_output=True,
        text=True,
        timeout=15,
        env={**ENV, "HOME": str(home)},
    )


def bash(command, cwd):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}


def enter_worktree(tool_input, cwd):
    return {"tool_name": "EnterWorktree", "tool_input": tool_input, "cwd": str(cwd)}


def journal(home):
    path = home / ".claude" / "hook-stats" / "blocks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


BLOCKED = [
    # checkout / switch
    "git checkout -b feat/gigaam",
    "git checkout -B hotfix",
    "git checkout --orphan=docs-site",
    "git checkout --orphan docs-site",
    "git checkout -b x -- file",
    "git switch -c lazy-fox",
    "git switch --create=x",
    "git switch -cx",
    # prefixes, global options, chains
    "git -C /tmp/r switch -c x",
    "git add -A && git checkout -b x",
    "cd /tmp; git switch -c x",
    "VAR=1 git checkout -b x",
    "command git checkout -b x",
    "/usr/bin/git checkout -b x",
    "rtk proxy git switch -c x",
    # branch (forms 3, 6)
    "git branch new-thing",
    "git branch -f new-thing main",
    "git branch -m old new-thing",
    "git branch -m renamed",
    "git branch --copy a b",
    # worktree add (forms 4, 5)
    "git worktree add -b feat/x ../wt",
    "git worktree add ../lazy-fox",
    "git worktree add --orphan ../lazy-fox",
    "git worktree add --reason r ../lazy-fox",
    # several lines
    "cd /tmp/r\ngit checkout -b x",
    "git status\ngit switch -c lazy-fox",
    "git checkout \\\n  -b x",
    # operators glued to the words around them
    "git status&&git checkout -b bad",
    "git status;git checkout -b bad",
    "true|git checkout -b bad",
    # a here-string is one word: the rest of the line is still checked
    "printf foo <<< bar && git switch -c bad",
    # grouped short options
    "git switch -qc bad",
    "git switch -qcbad",
    "git checkout -qb bad",
    "git checkout -fB bad",
    "git branch -fm feat/branch-old bad",
]

ALLOWED = [
    # names with the segment
    "git checkout -b feat/branch-x",
    "git switch -c fix/branch-y",
    # not creating
    "git checkout main",
    "git checkout -- file",
    "git checkout --track origin/lazy-fox",
    "git switch lazy-fox",
    "git push -u origin HEAD",
    "git status",
    # text, not commands
    'git commit -m "use git checkout -b x"',
    "echo 'git checkout -b x'",
    'grep -rn "checkout -b" docs/',
    # empty or unparsable
    "ls",
    "",
    "git checkout -b 'unbalanced",
    "git checkout -b",
    # branch and worktree add, names with the segment
    "git branch docs/branch-z",
    "git branch -m old feat/branch-new",
    "git worktree add ../feat-branch-x",
    "git worktree add -b feat/branch-x ../wt",
    # branch and worktree add, not creating
    "git branch -d lazy-fox",
    "git branch -D x",
    "git branch --list",
    "git branch",
    "git branch -u origin/main",
    "git branch --show-current",
    "git worktree remove ../wt",
    "git worktree add --detach ../wt",
    "git worktree add ../wt lazy-fox",
    "git worktree list",
    # several lines: a quoted newline and a heredoc body are text
    'git commit -m "first line\ngit checkout -b x"',
    "cat <<EOF\ngit checkout -b x\nEOF",
    "echo hi\ngit status",
    # glued operators, ordinary commands
    "git status&&git log",
    "echo a|grep a",
    "git branch -d old",
    "git branch -D old",
    "git worktree add --detach x",
    'cat <<< "git checkout -b x"',
    # grouped short options: deleting, listing, or a name with the segment
    "git branch -df old",
    "git branch -Dr x",
    "git switch -qc feat/branch-x",
    "git checkout -qb feat/branch-x",
    "git switch -qf main",
    "git checkout -fq main",
]


@pytest.mark.parametrize("command", BLOCKED)
def test_branch_without_segment_is_denied(command, repo, home):
    result = run_hook(bash(command, repo), home)
    assert result.returncode == 2, f"hook allowed: {command!r}"
    assert "N-BRANCH" in result.stderr


@pytest.mark.parametrize("command", ALLOWED)
def test_ordinary_command_is_allowed(command, repo, home):
    result = run_hook(bash(command, repo), home)
    assert result.returncode == 0, f"hook blocked: {command!r}"
    assert result.stdout == "" and result.stderr == ""
    assert journal(home) == []


def test_deny_message_names_the_form_and_the_name(repo, home):
    result = run_hook(bash("git checkout -b lazy-fox", repo), home)
    assert "'lazy-fox'" in result.stderr
    assert "<type>/branch-<slug>" in result.stderr
    assert "feat, fix, docs, style, refactor, test, chore, perf, build, ci" in result.stderr
    assert "N-BRANCH: off" in result.stderr
    assert "machine-readable" not in result.stderr


def test_every_offending_name_is_listed(repo, home):
    result = run_hook(bash("git checkout -b a && git switch -c b", repo), home)
    assert "'a, b'" in result.stderr


def test_deny_is_journaled(repo, home):
    run_hook(bash("git checkout -b lazy-fox", repo), home)
    (record,) = journal(home)
    assert record["hook"] == "branch-name-check"
    assert record["kind"] == "bash-git"
    assert record["command"] == "git checkout -b lazy-fox"


@pytest.mark.parametrize("stdin", ["", "not json", "[]", "42", "{}", '{"tool_name": "Bash"}'])
def test_malformed_input_is_allowed(stdin, home):
    assert run_hook(stdin, home).returncode == 0


def test_other_tools_are_ignored(repo, home):
    payload = {"tool_name": "Read", "tool_input": {"command": "git checkout -b x", "name": "x"}, "cwd": str(repo)}
    assert run_hook(payload, home).returncode == 0


@pytest.mark.parametrize("tool_input", [{"name": "lazy-fox"}, {}, {"name": ""}])
def test_worktree_without_segment_is_denied(tool_input, repo, home):
    result = run_hook(enter_worktree(tool_input, repo), home)
    assert result.returncode == 2
    assert "EnterWorktree" in result.stderr


@pytest.mark.parametrize("tool_input", [{"name": "feat/branch-x"}, {"name": "feat+branch-x"}, {"path": "/tmp/wt"}])
def test_worktree_with_segment_or_path_is_allowed(tool_input, repo, home):
    assert run_hook(enter_worktree(tool_input, repo), home).returncode == 0


def test_worktree_deny_is_journaled(repo, home):
    run_hook(enter_worktree({"name": "lazy-fox"}, repo), home)
    (record,) = journal(home)
    assert record["kind"] == "enter-worktree"
    assert record["command"] == "lazy-fox"


def write_agents(repo_path, overrides):
    """AGENTS.md whose `## Other` section also carries an `off` line that must never count."""
    (repo_path / "AGENTS.md").write_text(
        f"# Project\n\n## Naming overrides\n\n{overrides}\n\n## Other\n\nN-BRANCH: off\n"
    )
    return repo_path


def test_override_off_allows_and_leaves_no_journal(tmp_path, home):
    repo_path = write_agents(make_repo(tmp_path / "r"), "N-BRANCH: off")
    assert run_hook(bash("git checkout -b lazy-fox", repo_path), home).returncode == 0
    assert journal(home) == []


def test_other_override_text_keeps_the_check_and_says_so(tmp_path, home):
    repo_path = write_agents(make_repo(tmp_path / "r"), "N-BRANCH: <type>-branch-<slug>")
    result = run_hook(bash("git checkout -b lazy-fox", repo_path), home)
    assert result.returncode == 2
    assert "only `N-BRANCH: off` is machine-readable" in result.stderr


def test_off_outside_the_overrides_section_is_ignored(tmp_path, home):
    repo_path = write_agents(make_repo(tmp_path / "r"), "N-DOCS: x")
    result = run_hook(bash("git checkout -b lazy-fox", repo_path), home)
    assert result.returncode == 2
    assert "machine-readable" not in result.stderr


def test_override_is_read_from_the_repository_root(tmp_path, home):
    repo_path = write_agents(make_repo(tmp_path / "r"), "N-BRANCH: off")
    sub = repo_path / "src"
    sub.mkdir()
    assert run_hook(bash("git checkout -b lazy-fox", sub), home).returncode == 0


def test_outside_a_repository_the_check_still_applies(tmp_path, home):
    assert run_hook(bash("git checkout -b feat/branch-x", tmp_path), home).returncode == 0
    assert run_hook(bash("git checkout -b lazy-fox", tmp_path), home).returncode == 2
