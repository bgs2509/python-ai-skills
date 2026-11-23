"""Regression suite for the settings.json render in install-claude-symlinks.sh.

Claude Code runs each hook `command` through a shell, so the rendered
{{CLAUDE_HOME}} path must survive word splitting: a Claude home with a space
used to split and the hook failed with exit 126 (bd python-ai-skills-4nb).

Every run redirects HOME, CLAUDE_HOME, CODEX_HOME, PI_HOME and XDG_CONFIG_HOME
into a throwaway directory, so the real ~/.claude, ~/.codex, ~/.pi and
~/.config stay untouched.

Run: pytest scripts/test_install_claude_symlinks.py
"""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent / "install-claude-symlinks.sh"


def run_installer(
    base: Path,
    claude_home: Path,
    extra_env: dict[str, str] | None = None,
    installer: Path = INSTALLER,
) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "HOME": str(base / "home"),
        "CLAUDE_HOME": str(claude_home),
        "CODEX_HOME": str(base / "home" / ".codex"),
        "PI_HOME": str(base / "home" / ".pi" / "agent"),
        "XDG_CONFIG_HOME": str(base / "xdg"),
        **(extra_env or {}),
    }
    return subprocess.run(
        ["bash", str(installer)], env=env, capture_output=True, text=True, timeout=120
    )


def hook_commands(settings: dict) -> list[str]:
    return [
        hook["command"]
        for groups in settings["hooks"].values()
        for group in groups
        for hook in group["hooks"]
        if hook.get("type") == "command"
    ]


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> tuple[Path, dict]:
    base = tmp_path_factory.mktemp("render")
    claude_home = base / "claude home"
    result = run_installer(base, claude_home)
    assert result.returncode == 0, result.stderr
    return claude_home, json.loads((claude_home / "settings.json").read_text())


def test_every_hook_path_is_one_shell_word(rendered):
    claude_home, settings = rendered
    commands = [c for c in hook_commands(settings) if str(claude_home) in c]
    assert commands, "template declares no hook commands under CLAUDE_HOME"
    for command in commands:
        words = [w for w in shlex.split(command) if str(claude_home) in w]
        assert len(words) == 1, f"path split into several words: {command}"
        assert Path(words[0]).is_file(), f"hook path does not exist: {words[0]}"


@pytest.mark.parametrize("char", ["'", '"', "\\", "|", "&", "\n"])
def test_unsafe_claude_home_is_refused(tmp_path, char):
    result = run_installer(tmp_path, tmp_path / f"bad{char}home")
    assert result.returncode != 0
    assert "CLAUDE_HOME" in result.stderr


@pytest.fixture
def skill_homes(tmp_path):
    homes = [tmp_path / "claude home", tmp_path / "home" / ".codex", tmp_path / "home" / ".pi" / "agent"]
    for home in homes:
        (home / "skills").mkdir(parents=True)
    return homes


def test_every_client_gets_the_same_flat_inventory(tmp_path, skill_homes):
    repo = INSTALLER.parent.parent
    files = list(repo.glob("Skills/*/*/SKILL.md"))
    expected = {f.parent.name: f.parent for f in files}
    assert len(files) == len(expected) == 50
    assert not list(repo.glob("*/SKILL.md"))
    for _ in range(2):
        result = run_installer(tmp_path, skill_homes[0])
        assert result.returncode == 0, result.stderr
        for home in skill_homes:
            actual = {p.name: p for p in (home / "skills").iterdir()}
            assert actual.keys() == expected.keys()
            assert all(p.is_symlink() and p.resolve() == expected[name] for name, p in actual.items())


def test_upgrade_retires_only_our_legacy_links(tmp_path, skill_homes):
    repo = INSTALLER.parent.parent
    custom = tmp_path / "custom"
    custom.mkdir()
    for home in skill_homes:
        old = home / "skills"
        (old / "_testing").symlink_to(repo / "_testing")
        (old / "architecture").symlink_to(repo / "architecture")
        (old / "testing").symlink_to(repo / "Skills" / "another-topic" / "testing")
        (old / "_init").symlink_to(repo / "_init")
        (old / "_logging").symlink_to(custom)
        (old / "_docker").mkdir()
    result = run_installer(tmp_path, skill_homes[0])
    assert result.returncode == 0, result.stderr
    for home in skill_homes:
        installed = home / "skills"
        assert (installed / "testing").resolve() == repo / "Skills/python-development/testing"
        assert (installed / "architecture").resolve() == repo / "Skills/python-development/architecture"
        assert (installed / "python-init" / "SKILL.md").is_file()
        assert not (installed / "init").exists()
        assert not (installed / "_testing").is_symlink()
        assert not (installed / "_init").is_symlink()
        assert (installed / "_logging").resolve() == custom
        assert (installed / "_docker").is_dir()


@pytest.mark.parametrize("kind", ["link", "directory", "file"])
def test_collision_aborts_before_touching_any_skill(tmp_path, skill_homes, kind):
    dest = skill_homes[-1] / "skills" / "testing"
    if kind == "link":
        dest.symlink_to(tmp_path / "external")
    elif kind == "directory":
        dest.mkdir()
    else:
        dest.write_text("unmanaged")
    result = run_installer(tmp_path, skill_homes[0])
    assert result.returncode != 0
    assert "skill destination is not owned" in result.stderr
    assert dest.exists() or dest.is_symlink()
    assert not list((skill_homes[0] / "skills").iterdir())


@pytest.fixture
def sample_installer(tmp_path):
    installer = tmp_path / "sample-repo" / "scripts" / INSTALLER.name
    installer.parent.mkdir(parents=True)
    shutil.copyfile(INSTALLER, installer)
    (installer.parent.parent / "claude-home").symlink_to(INSTALLER.parent.parent / "claude-home")
    return installer


def write_skill(repo, rel, name):
    file = repo / rel / "SKILL.md"
    file.parent.mkdir(parents=True)
    file.write_text(f"---\nname: {name}\ndescription: Sample skill.\n---\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("rel", "name", "diagnostic"),
    [
        ("Skills/other/sample", "sample", "duplicate skill name"),
        ("Skills/other/not-sample", "sample", "invalid skill directory or name"),
        ("Skills/other/_invalid", "_invalid", "invalid skill directory or name"),
    ],
)
def test_invalid_inventory_stops_before_install(tmp_path, sample_installer, rel, name, diagnostic):
    repo = sample_installer.parent.parent
    write_skill(repo, "Skills/example/sample", "sample")
    write_skill(repo, rel, name)
    home = tmp_path / "claude"
    result = run_installer(tmp_path, home, installer=sample_installer)
    assert result.returncode != 0
    assert diagnostic in result.stderr
    assert not (home / "skills").exists()


def test_discovers_only_one_category_level(tmp_path, sample_installer):
    repo = sample_installer.parent.parent
    write_skill(repo, "Skills/example/sample", "sample")
    write_skill(repo, "Skills/example/sample/assets/fixture", "fixture")
    write_skill(repo, "outside", "outside")
    home = tmp_path / "claude"
    result = run_installer(tmp_path, home, installer=sample_installer)
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in (home / "skills").iterdir()) == ["sample"]


def test_pi_block_is_opt_out(tmp_path):
    result = run_installer(tmp_path, tmp_path / "claude home", {"PI_HOME": "/dev/null"})
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "home" / ".pi" / "agent" / "skills").exists()
