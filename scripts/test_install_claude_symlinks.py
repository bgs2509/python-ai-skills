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
import subprocess
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent / "install-claude-symlinks.sh"


def run_installer(
    base: Path, claude_home: Path, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "HOME": str(base / "home"),
        "CLAUDE_HOME": str(claude_home),
        "CODEX_HOME": str(base / "no-codex"),
        "XDG_CONFIG_HOME": str(base / "xdg"),
        **(extra_env or {}),
    }
    return subprocess.run(
        ["bash", str(INSTALLER)], env=env, capture_output=True, text=True, timeout=120
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


def test_pi_skills_are_linked(tmp_path):
    """Every repo skill dir is linked into the pi agent dir (bd python-ai-skills-4mw)."""
    claude_home = tmp_path / "claude home"
    (tmp_path / "home" / ".pi" / "agent").mkdir(parents=True)  # pi installed
    result = run_installer(tmp_path, claude_home)
    assert result.returncode == 0, result.stderr
    repo = INSTALLER.parent.parent
    skills = sorted(p.name for p in repo.iterdir() if (p / "SKILL.md").is_file())
    assert len(skills) == 50, f"expected 50 repo skills, found {len(skills)}"
    pi_skills = tmp_path / "home" / ".pi" / "agent" / "skills"
    for name in skills:
        link = pi_skills / name
        assert link.is_symlink(), f"pi skill link missing: {name}"
        assert link.resolve() == (repo / name).resolve(), f"wrong pi link target: {name}"


def test_pi_block_is_opt_out(tmp_path):
    result = run_installer(tmp_path, tmp_path / "claude home", {"PI_HOME": "/dev/null"})
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "home" / ".pi" / "agent" / "skills").exists()
