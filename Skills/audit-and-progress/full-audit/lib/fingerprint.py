"""Stable fingerprints for audit findings.

Two fingerprints per finding:
- strict: sha1(check_id | file | line_bucket | message_canonical)
- loose:  sha1(check_id | module_top | message_canonical)  — rename-tolerant

`line_bucket = line // 5` so ±5-line shifts don't break match.
`message_canonical` lower-cased with numbers, hex IDs, and file paths normalized.
"""
from __future__ import annotations

import hashlib
import re

_NUM_RE = re.compile(r"\b\d+\b")
_HEX_RE = re.compile(r"\b[a-f0-9]{7,}\b|\b[A-F0-9-]{20,}\b")
_PATH_RE = re.compile(r"[/\w_.-]+\.(?:py|md|xml|yml|yaml|toml|sh)\b")


def line_bucket(line: int) -> int:
    return int(line) // 5


def normalize_message(msg: str) -> str:
    s = msg.strip().lower()
    s = _PATH_RE.sub("<path>", s)
    s = _HEX_RE.sub("<id>", s)
    s = _NUM_RE.sub("N", s)
    return " ".join(s.split())


def _module_top(file: str) -> str:
    parts = file.replace("\\", "/").split("/")
    if "src" in parts:
        i = parts.index("src")
        if i + 1 < len(parts):
            return parts[i + 1]
    return parts[0] if parts else ""


def compute_fingerprint(check_id: str, file: str, line: int, message: str) -> str:
    key = f"{check_id}|{file}|{line_bucket(line)}|{normalize_message(message)}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def compute_fingerprint_loose(check_id: str, file: str, message: str) -> str:
    key = f"{check_id}|{_module_top(file)}|{normalize_message(message)}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()
