"""Tests for git-finish-state.sh — the one-call, read-only state probe of /git-finish."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "git-finish-state.sh"
KEYS = ["mode", "branch", "base", "main_root", "worktree", "remote", "branch_on_remote", "ahead_of_origin"]


@pytest.fixture
def env(tmp_path):
    # A minimal environment: no inherited GIT_DIR / GIT_INDEX_FILE / GIT_WORK_TREE can
    # redirect the fixtures into the developer's own repository.
    return {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd, env, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True)


def init(path, env, *extra):
    path.mkdir(parents=True, exist_ok=True)
    git(path, env, "init", "-q", "-b", "main", *extra)
    (path / "a.txt").write_text("a\n")
    git(path, env, "add", "a.txt")
    git(path, env, "commit", "-qm", "init")
    return path


@pytest.fixture
def repo(tmp_path, env):
    return init(tmp_path / "repo", env)


def probe(cwd, env, *args, timeout=20):
    out = subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True,
                         env=env, timeout=timeout)
    assert out.returncode == 0, out.stderr
    head = out.stdout.split("--- log", 1)[0]
    fields, errors = {}, []
    for line in head.splitlines():
        k, _, v = line.partition("=")
        if k == "error":
            errors.append(v)
        else:
            fields[k] = v
    return fields, errors, out.stdout


def test_outside_git_prints_the_full_schema(tmp_path, env):
    d = tmp_path / "plain"
    d.mkdir()
    fields, _, out = probe(d, env, ".")
    assert fields["mode"] == "no-git"
    assert list(fields) == KEYS
    assert "--- log" in out and "--- bd in_progress" in out and "bd: not on PATH" in out


def test_base_branch_without_remote(repo, env):
    fields, errors, _ = probe(repo, env, ".")
    assert fields["mode"] == "base" and fields["base"] == "main" and fields["branch"] == "main"
    assert fields["remote"] == "no" and fields["worktree"] == ""
    assert errors == []


def test_feature_branch_in_main_clone_has_no_removable_worktree(repo, env):
    git(repo, env, "checkout", "-qb", "feat")
    fields, _, _ = probe(repo, env, ".")
    assert fields["mode"] == "branch" and fields["branch"] == "feat"
    assert fields["main_root"] == str(repo) and fields["worktree"] == ""


def test_feature_branch_in_linked_worktree_is_reported(repo, env, tmp_path):
    wt = tmp_path / "wt"
    git(repo, env, "worktree", "add", "-q", "-b", "feat", str(wt))
    fields, _, _ = probe(wt, env, ".")
    assert fields["mode"] == "branch"
    assert fields["worktree"] == str(wt) and fields["main_root"] == str(repo)


def test_separate_git_dir_is_not_mistaken_for_a_worktree(tmp_path, env):
    work = init(tmp_path / "work", env, "--separate-git-dir", str(tmp_path / "meta.git"))
    git(work, env, "checkout", "-qb", "feat")
    fields, _, _ = probe(work, env, ".")
    assert fields["main_root"] == str(work)
    assert fields["worktree"] == ""


def test_detached_head(repo, env):
    sha = git(repo, env, "rev-parse", "HEAD").stdout.strip()
    git(repo, env, "checkout", "-q", sha)
    assert probe(repo, env, ".")[0]["mode"] == "detached"


def test_unknown_base_is_its_own_mode(tmp_path, env):
    r = tmp_path / "r"
    r.mkdir()
    git(r, env, "init", "-q", "-b", "trunk")
    (r / "a").write_text("a")
    git(r, env, "add", "a")
    git(r, env, "commit", "-qm", "i")
    git(r, env, "checkout", "-qb", "feat")
    fields, _, _ = probe(r, env, ".")
    assert fields["mode"] == "unknown-base" and fields["base"] == ""


def test_base_override_wins(repo, env):
    git(repo, env, "checkout", "-qb", "develop")
    git(repo, env, "checkout", "-qb", "feat")
    fields, _, _ = probe(repo, env, ".", "--base", "develop")
    assert fields["base"] == "develop" and fields["mode"] == "branch"


def test_lone_base_flag_terminates_with_an_error(repo, env):
    fields, errors, _ = probe(repo, env, ".", "--base", timeout=5)
    assert "--base needs a branch name" in errors
    assert fields["base"] == "main"


def test_remote_state_from_tracking_refs_only(repo, env, tmp_path):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], env=env, check=True)
    git(repo, env, "remote", "add", "origin", str(bare))
    git(repo, env, "push", "-q", "-u", "origin", "main")
    (repo / "b.txt").write_text("b\n")
    git(repo, env, "add", "b.txt")
    git(repo, env, "commit", "-qm", "two")
    git(repo, env, "checkout", "-qb", "topic")
    git(repo, env, "push", "-q", "origin", "topic:refs/heads/foo/topic")  # same short name, other ref
    fields, _, _ = probe(repo, env, ".")
    assert fields["remote"] == "yes"
    assert fields["ahead_of_origin"] == "1"
    assert fields["branch_on_remote"] == "no"   # exact refs/remotes/origin/topic only, no glob
    git(repo, env, "push", "-q", "origin", "topic")
    assert probe(repo, env, ".")[0]["branch_on_remote"] == "yes"


def test_unreachable_remote_is_never_contacted(repo, env):
    git(repo, env, "remote", "add", "origin", "ssh://nonexistent.invalid/x.git")
    git(repo, env, "config", "core.sshCommand", "touch SSH_WAS_CALLED; false")
    fields, _, _ = probe(repo, env, ".", timeout=10)
    assert fields["remote"] == "yes" and fields["ahead_of_origin"] == "unknown"
    assert not (repo / "SSH_WAS_CALLED").exists()


def test_dash_directory_argument_is_not_cd_minus(repo, env, tmp_path):
    d = repo / "-"
    d.mkdir()
    fields, _, out = probe(repo, env, "-")
    assert out.startswith("mode=")
    assert fields["mode"] == "base"


def test_log_block_and_no_status_block(repo, env):
    (repo / "new.txt").write_text("x\n")
    _, _, out = probe(repo, env, ".")
    assert "init" in out.split("--- log", 1)[1]
    assert "--- status" not in out


def test_probe_writes_nothing(repo, env):
    before = git(repo, env, "status", "--porcelain").stdout
    probe(repo, env, ".")
    assert git(repo, env, "status", "--porcelain").stdout == before


def test_base_value_that_is_a_flag_is_rejected(repo, env):
    fields, errors, _ = probe(repo, env, ".", "--base", "--no-push")
    assert fields["base"] == "main"
    assert "--base needs a branch name" in errors


def test_failing_mandatory_git_command_is_an_error_not_a_state(repo, env, tmp_path):
    fake = tmp_path / "fakebin"
    fake.mkdir()
    real = subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip()
    (fake / "git").write_text(f'#!/bin/bash\nfor a in "$@"; do [ "$a" = --show-current ] && exit 42; done\nexec {real} "$@"\n')
    (fake / "git").chmod(0o755)
    fields, errors, _ = probe(repo, {**env, "PATH": f"{fake}:/usr/bin:/bin"}, ".")
    assert fields["mode"] == "error"
    assert any("--show-current" in e for e in errors)


def test_bd_is_not_run_after_a_failed_cd(tmp_path, env):
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "bd").write_text('#!/bin/bash\necho "BD RAN IN $PWD"\n')
    (fake / "bd").chmod(0o755)
    _, errors, out = probe(tmp_path, {**env, "PATH": f"{fake}:/usr/bin:/bin"}, str(tmp_path / "missing"))
    assert "BD RAN" not in out and "bd: skipped" in out


def test_bd_listing_is_unlimited(repo, env, tmp_path):
    fake = tmp_path / "fakebin"
    fake.mkdir()
    (fake / "bd").write_text('#!/bin/bash\necho "ARGS $*"\n')
    (fake / "bd").chmod(0o755)
    _, _, out = probe(repo, {**env, "PATH": f"{fake}:/usr/bin:/bin"}, ".")
    assert "--limit 0" in out
