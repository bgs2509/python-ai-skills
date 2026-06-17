#!/usr/bin/env python3
"""Anti-hallucination Stop hook.

Reads Stop event JSON from stdin, scans last assistant message for
UPPER_SNAKE identifiers (>=8 chars, >=2 underscores), and blocks the
turn if any such identifier never appears in tool results, tool inputs,
or user messages of the current session.

See ~/.claude/CLAUDE.md → "Anti-Hallucination Protocol".
"""
import json
import pathlib
import re
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("stop_hook_active"):
        return 0

    transcript_path = data.get("transcript_path")
    if not transcript_path:
        return 0
    p = pathlib.Path(transcript_path)
    if not p.exists():
        return 0

    events = []
    for line in p.read_text(errors="ignore").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    last_text = ""
    for ev in reversed(events):
        if ev.get("type") != "assistant":
            continue
        msg = ev.get("message", {})
        parts = []
        for block in msg.get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        if parts:
            last_text = "\n".join(parts)
            break

    if not last_text:
        return 0

    stripped = re.sub(r"```.*?```", "", last_text, flags=re.DOTALL)
    stripped = re.sub(r"`[^`]*`", "", stripped)

    candidates = {
        m for m in re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,}\b", stripped)
        if len(m) >= 8
    }

    IGNORE = {
        "MODULE_CONTRACT", "MODULE_MAP", "MODULE_ID", "USER_APPROVAL",
        "BLOCK_NAME", "FILE_NAME", "VERSION_BUMP", "CHANGE_SUMMARY",
        "LAST_CHANGE", "START_BLOCK", "END_BLOCK",
        "START_MODULE_CONTRACT", "END_MODULE_CONTRACT",
        "START_MODULE_MAP", "END_MODULE_MAP",
        "START_CONTRACT", "END_CONTRACT",
        "START_CHANGE_SUMMARY", "END_CHANGE_SUMMARY",
        "SIDE_EFFECTS", "CRITICAL_RULES", "ANTI_HALLUCINATION",
    }
    candidates -= IGNORE
    if not candidates:
        return 0

    chunks = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ev_type = ev.get("type")
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        is_assistant = ev_type == "assistant"
        content = msg.get("content")
        if isinstance(content, str):
            if not is_assistant:
                chunks.append(content)
            continue
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                # Assistant's own prose is NOT evidence — that's what we're checking.
                if not is_assistant:
                    chunks.append(b.get("text", "") or "")
            elif t == "tool_result":
                c = b.get("content", "")
                if isinstance(c, str):
                    chunks.append(c)
                elif isinstance(c, list):
                    for sub in c:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            chunks.append(sub.get("text", "") or "")
            elif t == "tool_use":
                inp = b.get("input", {})
                try:
                    chunks.append(json.dumps(inp))
                except Exception:
                    pass

    verified = "\n".join(chunks)
    unverified = sorted(c for c in candidates if c not in verified)
    if not unverified:
        return 0

    reason = (
        "ANTI-HALLUCINATION GATE BLOCKED YOUR RESPONSE.\n\n"
        "Your last message named these UPPER_SNAKE identifiers that do NOT "
        "appear in any tool result, file Read, tool input, or user message "
        "in this session:\n"
        "  " + ", ".join(unverified[:15]) + "\n\n"
        "Per ~/.claude/CLAUDE.md → 'Anti-Hallucination Protocol' you MUST "
        "NOT name concrete identifiers without verification. Required action "
        "NOW:\n"
        "  1. For each unverified identifier — run Read/Grep/Glob to confirm "
        "it exists in the project, OR run `<tool> --help` to confirm it's a "
        "real CLI flag/var.\n"
        "  2. If it does NOT exist — explicitly retract it in a corrected "
        "reply, marking the item as a hypothesis ('возможно стоило бы ввести "
        "X') rather than a fact.\n"
        "  3. If it DOES exist — re-state with citation (file:line) so the "
        "user can audit.\n\n"
        "Do NOT bypass this hook by renaming/masking the token. The point "
        "is epistemic discipline, not regex evasion."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
