"""Tests for git-finish-state.sh — the one-call, read-only state probe of /git-finish."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "git-finish-state.sh"


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def env(tmp_path):
    e = dict(os.environ)
    e.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
              "GIT_COMMITTER_EMAIL": "t@t", "HOME": str(tmp_path), "GIT_CONFIG_NOSYSTEM": "1",
              "PATH": "/usr/bin:/bin"})  # no bd on PATH: the probe must cope
    return e


@pytest.fixture
def repo(tmp_path, env):
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=r, check=True, env=env)
    (r / "a.txt").write_text("a\n")
    subprocess.run(["git", "add", "a.txt"], cwd=r, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=r, check=True, env=env)
    return r


def probe(cwd, env, *args):
    out = subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env)
    assert out.returncode == 0, out.stderr
    fields = {}
    for line in out.stdout.split("--- ", 1)[0].splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            fields[k] = v
    return fields, out.stdout


def test_outside_git_is_no_git_mode(tmp_path, env):
    d = tmp_path / "plain"
    d.mkdir()
    fields, _ = probe(d, env, ".")
    assert fields["mode"] == "no-git"


def test_base_branch_without_remote(repo, env):
    fields, _ = probe(repo, env, ".")
    assert fields["mode"] == "base"
    assert fields["base"] == "main" and fields["branch"] == "main"
    assert fields["remote"] == "no"
    assert fields["worktree"] == ""


def test_feature_branch_in_main_clone_has_no_removable_worktree(repo, env):
    subprocess.run(["git", "checkout", "-qb", "feat"], cwd=repo, check=True, env=env)
    fields, _ = probe(repo, env, ".")
    assert fields["mode"] == "branch" and fields["branch"] == "feat" and fields["base"] == "main"
    assert fields["main_root"] == str(repo)
    assert fields["worktree"] == ""


def test_feature_branch_in_linked_worktree_is_reported(repo, env, tmp_path):
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", "-b", "feat", str(wt)], cwd=repo, check=True, env=env)
    fields, _ = probe(wt, env, ".")
    assert fields["mode"] == "branch"
    assert fields["worktree"] == str(wt)
    assert fields["main_root"] == str(repo)


def test_detached_head(repo, env):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "checkout", "-q", sha], cwd=repo, check=True, env=env)
    fields, _ = probe(repo, env, ".")
    assert fields["mode"] == "detached"


def test_base_override_wins(repo, env):
    subprocess.run(["git", "checkout", "-qb", "develop"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "checkout", "-qb", "feat"], cwd=repo, check=True, env=env)
    fields, _ = probe(repo, env, ".", "--base", "develop")
    assert fields["base"] == "develop" and fields["mode"] == "branch"


def test_remote_ahead_count_and_branch_on_remote(repo, env, tmp_path):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, env=env)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=repo, check=True, env=env)
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=repo, check=True, env=env)
    (repo / "b.txt").write_text("b\n")
    subprocess.run(["git", "add", "b.txt"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "two"], cwd=repo, check=True, env=env)
    fields, _ = probe(repo, env, ".")
    assert fields["remote"] == "yes"
    assert fields["ahead_of_origin"] == "1"
    assert fields["branch_on_remote"] == "yes"


def test_status_log_and_bd_blocks(repo, env):
    (repo / "new.txt").write_text("x\n")
    _, out = probe(repo, env, ".")
    assert "--- status" in out and "?? new.txt" in out
    assert "--- log" in out and "init" in out
    assert "--- bd in_progress" in out


def test_probe_writes_nothing(repo, env):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
    probe(repo, env, ".")
    after = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
    assert before == after
