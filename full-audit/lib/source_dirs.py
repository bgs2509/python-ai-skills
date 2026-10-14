#!/usr/bin/env python3
"""Print the project's source dirs (one per line) for the full-audit checks."""
from __future__ import annotations

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


def _declared(cfg: dict, key: tuple[str, ...]) -> list[str]:
    for part in key:
        cfg = cfg.get(part) if isinstance(cfg, dict) else None
    if isinstance(cfg, str):  # mypy also accepts a comma-separated string
        cfg = [p.strip() for p in cfg.split(",")]
    if not isinstance(cfg, list):
        return []
    return [p for p in cfg if isinstance(p, str)]


def derive(root: Path) -> list[str]:
    """Return source dirs relative to root: src/, declared paths, or top-level packages."""
    if (root / "src").is_dir():
        return ["src"]
    try:
        cfg = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        cfg = {}
    for key in KEYS:
        found = [p for p in _declared(cfg, key) if (root / p).is_dir()]
        if found:
            return found
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and d.name not in EXCLUDE and (d / "__init__.py").is_file()
    )


def main() -> int:
    for d in derive(Path.cwd()):
        print(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
