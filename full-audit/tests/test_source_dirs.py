"""Tests for source_dirs.derive and the run.sh wiring."""
from pathlib import Path

import pytest

from source_dirs import derive, main

RUN_SH = Path(__file__).resolve().parent.parent / "lib" / "run.sh"


def make(root: Path, dirs=(), pyproject: str | None = None, pkgs=()):
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    for d in pkgs:
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / "__init__.py").write_text("")
    if pyproject is not None:
        (root / "pyproject.toml").write_text(pyproject)
    return root


def test_src_wins_over_config(tmp_path):
    make(tmp_path, ["src", "backend"], '[tool.mypy]\nfiles = ["backend"]\n')
    assert derive(tmp_path) == ["src"]


def test_mypy_files_taro_shape(tmp_path):
    dirs = ["backend", "telegram_bot", "scheduler", "shared"]
    make(tmp_path, dirs, '[tool.mypy]\nfiles = ["backend", "telegram_bot", "scheduler", "shared"]\n')
    assert derive(tmp_path) == dirs


def test_coverage_run_source(tmp_path):
    make(tmp_path, ["app"], '[tool.coverage.run]\nsource = ["app"]\n')
    assert derive(tmp_path) == ["app"]


def test_interrogate_paths(tmp_path):
    make(tmp_path, ["pkg"], '[tool.interrogate]\npaths = ["pkg"]\n')
    assert derive(tmp_path) == ["pkg"]


def test_vulture_paths(tmp_path):
    make(tmp_path, ["pkg"], '[tool.vulture]\npaths = ["pkg"]\n')
    assert derive(tmp_path) == ["pkg"]


def test_missing_declared_dir_is_dropped(tmp_path):
    make(tmp_path, ["a"], '[tool.mypy]\nfiles = ["a", "gone"]\n')
    assert derive(tmp_path) == ["a"]


def test_all_declared_missing_tries_next_key(tmp_path):
    make(
        tmp_path,
        ["app"],
        '[tool.mypy]\nfiles = ["gone"]\n[tool.coverage.run]\nsource = ["app"]\n',
    )
    assert derive(tmp_path) == ["app"]


def test_probe_skips_excluded_dirs(tmp_path):
    make(tmp_path, ["docs", "data"], pkgs=["bot", "tests", ".venv", "scripts"])
    assert derive(tmp_path) == ["bot"]


def test_probe_ignores_dirs_without_init(tmp_path):
    make(tmp_path, ["plain"], pkgs=["bot"])
    assert derive(tmp_path) == ["bot"]


def test_nothing_returns_empty(tmp_path):
    assert derive(tmp_path) == []


def test_unparsable_pyproject_falls_through_to_probe(tmp_path):
    make(tmp_path, pyproject="[tool.mypy\nfiles = ", pkgs=["bot"])
    assert derive(tmp_path) == ["bot"]


def test_main_prints_nothing_when_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert capsys.readouterr().out == ""


def test_main_prints_one_dir_per_line(tmp_path, monkeypatch, capsys):
    make(tmp_path, pkgs=["a", "b"])
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert capsys.readouterr().out == "a\nb\n"


@pytest.mark.parametrize(
    "literal",
    ["--cov=src", "radon cc src", "radon mi src", "vulture src", "interrogate src"],
)
def test_run_sh_has_no_hardcoded_src(literal):
    assert literal not in RUN_SH.read_text(encoding="utf-8")


def test_run_sh_calls_helper():
    assert "source_dirs.py" in RUN_SH.read_text(encoding="utf-8")
