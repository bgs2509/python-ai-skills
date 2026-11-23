"""Shared helper: write finding JSON lines to a sidecar file from self-check scripts."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator


@contextmanager
def open_sidecar(path: Path | None) -> Iterator[IO[str] | None]:
    if path is None:
        yield None
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        yield f


def emit_finding(
    fp: IO[str] | None,
    check_id: str,
    file: str,
    line: int,
    severity: str,
    rule_id: str,
    message: str,
) -> None:
    if fp is None:
        return
    fp.write(json.dumps({
        "check_id": check_id,
        "file": file,
        "line": int(line),
        "severity": severity,
        "rule_id": rule_id,
        "message_raw": message,
    }) + "\n")
