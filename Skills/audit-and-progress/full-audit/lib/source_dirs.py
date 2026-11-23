#!/usr/bin/env python3
"""Print the project's source dirs (one per line) for the full-audit checks.

With --vulture DIR..., print the vulture arguments (one per line) instead.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

# Top-level dirs the __init__.py probe never reports as source.
EXCLUDE = frozenset({".venv", "tests", "docs", "data", "_output", "scripts"})
# pyproject keys that declare source paths, tried in order.
KEYS = (
    ("tool", "mypy", "files"),
    ("tool", "coverage", "run", "source"),
    ("tool", "interrogate", "paths"),
    ("tool", "vulture", "paths"),
)
# Fallback threshold when the project has no [tool.vulture] of its own.
VULTURE_MIN_CONFIDENCE = "80"


def _declared(cfg: dict, key: tuple[str, ...]) -> list[str]:
    for part in key:
        cfg = cfg.get(part) if isinstance(cfg, dict) else None
    if isinstance(cfg, str):  # mypy also accepts a comma-separated string
        cfg = [p.strip() for p in cfg.split(",")]
    if not isinstance(cfg, list):
        return []
    return [p for p in cfg if isinstance(p, str)]


def _pyproject(root: Path) -> dict:
    try:
        return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def derive(root: Path) -> list[str]:
    """Return source dirs relative to root: src/, declared paths, or top-level packages."""
    if (root / "src").is_dir():
        return ["src"]
    cfg = _pyproject(root)
    for key in KEYS:
        found = [p for p in _declared(cfg, key) if (root / p).is_dir()]
        if found:
            return found
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and d.name not in EXCLUDE and (d / "__init__.py").is_file()
    )


def vulture_args(root: Path, dirs: list[str]) -> list[str]:
    """Return vulture CLI args; CLI options override [tool.vulture], so pass none it sets."""
    section = _pyproject(root).get("tool", {}).get("vulture")
    if not isinstance(section, dict):
        return [*dirs, "--min-confidence", VULTURE_MIN_CONFIDENCE]
    return [] if section.get("paths") else list(dirs)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--vulture"]:
        lines = vulture_args(Path.cwd(), argv[1:])
    else:
        lines = derive(Path.cwd())
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
