"""Tests for the shared repo-sync core (project-sync/lib/sync.py).

Pure parsing + classification logic is tested directly; the subprocess-backed
``diagnose_repo`` is tested with an injected fake runner so no real git is touched.
"""
from __future__ import annotations

from sync import (
    RepoStatus,
    classify,
    diagnose_repo,
    parse_ahead_behind,
    parse_find_output,
    parse_status_porcelain,
    status_to_dict,
)


# --- parse_status_porcelain ------------------------------------------------

def test_porcelain_empty_means_clean():
    assert parse_status_porcelain("") == []
    assert parse_status_porcelain("\n") == []


def test_porcelain_lists_changed_files():
    out = " M src/app.py\n?? new.txt\nA  staged.py\n"
    assert parse_status_porcelain(out) == ["src/app.py", "new.txt", "staged.py"]


# --- parse_ahead_behind ----------------------------------------------------

def test_ahead_behind_parses_left_right_count():
    # `git rev-list --left-right --count @{u}...HEAD` => "<behind>\t<ahead>"
    assert parse_ahead_behind("0\t0\n") == (0, 0)
    assert parse_ahead_behind("3\t2\n") == (3, 2)


def test_ahead_behind_handles_spaces():
    assert parse_ahead_behind("1   4") == (1, 4)


# --- classify (the decision heart) -----------------------------------------

def test_classify_no_remote_takes_priority():
    assert classify(has_remote=False, dirty=True, ahead=5, behind=5) == "no_remote"


def test_classify_dirty_before_divergence():
    assert classify(has_remote=True, dirty=True, ahead=1, behind=1) == "dirty"


def test_classify_diverged():
    assert classify(has_remote=True, dirty=False, ahead=2, behind=3) == "diverged"


def test_classify_ahead_only():
    assert classify(has_remote=True, dirty=False, ahead=2, behind=0) == "ahead"


def test_classify_behind_only():
    assert classify(has_remote=True, dirty=False, ahead=0, behind=4) == "behind"


def test_classify_up_to_date():
    assert classify(has_remote=True, dirty=False, ahead=0, behind=0) == "up_to_date"


# --- diagnose_repo with an injected fake runner ----------------------------

class _FakeResult:
    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


def _make_runner(responses):
    """responses: dict mapping a command-key (first 3 args joined) -> _FakeResult."""

    def run(cmd, cwd=None):  # noqa: ARG001
        key = " ".join(cmd[:3])
        return responses.get(key, _FakeResult())

    return run


def test_diagnose_clean_repo_up_to_date():
    run = _make_runner({
        "git rev-parse --abbrev-ref": _FakeResult("main\n"),
        "git remote": _FakeResult("origin\n"),
        "git status --porcelain": _FakeResult(""),
        "git rev-list --left-right": _FakeResult("0\t0\n"),
    })
    st = diagnose_repo("/repo", run=run)
    assert isinstance(st, RepoStatus)
    assert st.state == "up_to_date"
    assert st.has_remote is True
    assert st.dirty_files == []
    assert st.branch == "main"


def test_diagnose_dirty_repo():
    run = _make_runner({
        "git rev-parse --abbrev-ref": _FakeResult("dev\n"),
        "git remote": _FakeResult("origin\n"),
        "git status --porcelain": _FakeResult(" M a.py\n"),
        "git rev-list --left-right": _FakeResult("0\t0\n"),
    })
    st = diagnose_repo("/repo", run=run)
    assert st.state == "dirty"
    assert st.dirty_files == ["a.py"]


def test_diagnose_no_remote_skips_ahead_behind():
    run = _make_runner({
        "git rev-parse --abbrev-ref": _FakeResult("main\n"),
        "git remote": _FakeResult("\n"),
        "git status --porcelain": _FakeResult(""),
    })
    st = diagnose_repo("/repo", run=run)
    assert st.has_remote is False
    assert st.state == "no_remote"
    assert st.ahead == 0 and st.behind == 0


# --- parse_find_output (projects-sync discovery) ---------------------------

def test_find_output_strips_git_suffix_and_sorts():
    out = "/home/u/b/.git\n/home/u/a/.git\n"
    assert parse_find_output(out) == ["/home/u/a", "/home/u/b"]


def test_find_output_ignores_blank_and_non_git_lines():
    out = "\n/home/u/proj/.git\nfind: permission denied\n"
    assert parse_find_output(out) == ["/home/u/proj"]


def test_find_output_dedups():
    out = "/x/.git\n/x/.git\n"
    assert parse_find_output(out) == ["/x"]


# --- status_to_dict (CLI serialization) ------------------------------------

def test_status_to_dict_adds_derived_dirty_flag():
    st = RepoStatus(
        path="/r", branch="main", has_remote=True,
        dirty_files=["a.py"], ahead=1, behind=0, state="dirty",
    )
    d = status_to_dict(st)
    assert d["dirty"] is True
    assert d["dirty_files"] == ["a.py"]
    assert d["state"] == "dirty"
    assert d["branch"] == "main"
