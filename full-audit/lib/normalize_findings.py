"""Per-tool parsers: raw tool output → list[Finding dict]."""
from __future__ import annotations

import json as _json
import re
from typing import Any

_RUFF_LINE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):\d+:\s+(?P<rule>[A-Z]\d+)\s+(?:\[\*\]\s+)?(?P<msg>.+?)\s*$"
)

_MYPY_LINE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):\s+error:\s+(?P<msg>.+?)(?:\s+\[(?P<rule>[\w-]+)\])?\s*$"
)


def parse_ruff(raw: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in raw.splitlines():
        m = _RUFF_LINE.match(line)
        if not m:
            continue
        out.append({
            "check_id": "01-ruff-check",
            "file": m.group("file"),
            "line": int(m.group("line")),
            "severity": "middle",
            "rule_id": m.group("rule"),
            "message_raw": m.group("msg"),
        })
    return out


def parse_mypy(raw: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in raw.splitlines():
        m = _MYPY_LINE.match(line)
        if not m:
            continue
        out.append({
            "check_id": "03-mypy",
            "file": m.group("file"),
            "line": int(m.group("line")),
            "severity": "middle",
            "rule_id": m.group("rule") or "mypy",
            "message_raw": m.group("msg"),
        })
    return out


def parse_gitleaks(raw: str) -> list[dict[str, Any]]:
    try:
        data = _json.loads(raw)
    except _json.JSONDecodeError:
        return []
    out: list[dict[str, Any]] = []
    for item in data or []:
        out.append({
            "check_id": "04-gitleaks",
            "file": item.get("File", "<unknown>"),
            "line": int(item.get("StartLine", 0)),
            "severity": "critical",
            "rule_id": item.get("RuleID", "leak"),
            "message_raw": item.get("Description", "secret detected"),
        })
    return out


_AI_HEADING = "## AI deep code analysis"
_AI_JSON_BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def parse_ai_section_json(report_md: str) -> list[dict[str, Any]]:
    if _AI_HEADING not in report_md:
        return []
    section = report_md.split(_AI_HEADING, 1)[1]
    next_h2 = section.find("\n## ")
    if next_h2 != -1:
        section = section[:next_h2]
    m = _AI_JSON_BLOCK.search(section)
    if not m:
        return []
    try:
        items = _json.loads(m.group(1))
    except _json.JSONDecodeError:
        return []
    out: list[dict[str, Any]] = []
    for it in items or []:
        out.append({
            "check_id": it.get("check_id", "ai-unknown"),
            "file": it["file"],
            "line": int(it.get("line", 0)),
            "severity": it.get("severity", "middle"),
            "rule_id": it.get("rule_id", ""),
            "message_raw": it.get("message", ""),
        })
    return out
