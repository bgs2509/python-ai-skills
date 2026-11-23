"""Shared pytest fixtures for full-audit skill tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "lib"))


@pytest.fixture
def golden_dir() -> Path:
    return Path(__file__).parent / "golden"


@pytest.fixture
def tmp_history(tmp_path: Path) -> Path:
    p = tmp_path / "audit-history.jsonl"
    p.touch()
    return p
