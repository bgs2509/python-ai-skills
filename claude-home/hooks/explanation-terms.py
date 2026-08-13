#!/usr/bin/env python3
"""Explanation-terms Stop hook.

Reads Stop event JSON from stdin, scans the last assistant message for
Latin-script coined terms inside Russian prose, and blocks the turn if such
a term never appears in tool results, tool inputs, or user messages of the
current session.

Two candidate shapes are checked:
  1. compound Latin tokens  -- index-time, foo_bar, write-through
  2. single Latin words in inline backticks  -- `boosting`, `analyzer`

Rationale: a term the model actually read somewhere leaves a trace in the
session (a doc fetch, a file Read, the user's own words). A term the model
constructed on the fly -- typically by completing the missing half of a real
pair, as in search-time -> index-time -- leaves no trace at all.

Deliberately NOT detected: Russian jargon ("прогон" instead of
"тестирование"). It is formally indistinguishable from any other Russian
word, so it stays on the rule in CLAUDE.md rather than on this hook.

Transcript-walking logic intentionally mirrors anti-hallucination.py instead
of importing from it: that hook is a working safety net and is left untouched.

See ~/.claude/CLAUDE.md -> "Explanation Protocol".
"""
import json
import pathlib
import re
import sys

# Everyday English compounds and stable industry terms that carry no
# explanatory weight -- flagging them would be noise, not signal.
IGNORE = {
    "e-mail", "up-to-date", "state-of-the-art", "read-only", "write-only",
    "open-source", "trade-off", "trade-offs", "best-practice", "step-by-step",
    "pre-commit", "post-commit", "pull-request", "code-review", "follow-up",
    "run-time", "real-time", "built-in", "opt-in", "opt-out", "fine-tune",
    "fine-tuning", "end-to-end", "out-of-the-box", "so-called", "well-known",
    "self-hosted", "multi-agent", "single-source", "docs-as-code",
}

# Minimum share of Cyrillic among letters for the message to count as Russian
# prose. Below this the answer is code or English, and the rule does not apply.
CYRILLIC_SHARE = 0.30


def last_assistant_text(events: list) -> str:
    for ev in reversed(events):
        if ev.get("type") != "assistant":
            continue
        parts = []
        for block in ev.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        if parts:
            return "\n".join(parts)
    return ""


def is_russian_prose(text: str) -> bool:
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", text))
    lat = len(re.findall(r"[a-zA-Z]", text))
    total = cyr + lat
    if total < 200:
        return False
    return cyr / total >= CYRILLIC_SHARE


def collect_candidates(text: str) -> set:
    # Fenced code blocks are real code, not prose terminology.
    prose = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Markdown links carry URLs full of hyphens.
    prose = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", prose)
    # Bare URLs.
    prose = re.sub(r"https?://\S+", " ", prose)

    candidates = set()

    # Shape 1: compound Latin tokens, in or out of backticks.
    for m in re.findall(r"\b[A-Za-z]{2,}(?:[-_][A-Za-z]{2,})+\b", prose):
        if len(m) >= 6:
            candidates.add(m)

    # Shape 2: single Latin word inside inline backticks.
    for m in re.findall(r"`([^`\n]{1,40})`", prose):
        token = m.strip()
        if re.fullmatch(r"[A-Za-z]{5,}", token):
            candidates.add(token)

    # Paths, calls, file names and flags are artifact names -- the
    # anti-hallucination hook owns those.
    return {
        c for c in candidates
        if not any(ch in c for ch in "./\\()[]{}<>:@$")
        and c.lower() not in IGNORE
    }


def verified_corpus(events: list) -> str:
    chunks = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        is_assistant = ev.get("type") == "assistant"
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
                # The assistant's own prose is not evidence -- it is the thing
                # under test.
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
                try:
                    chunks.append(json.dumps(b.get("input", {}), ensure_ascii=False))
                except Exception:
                    pass
    return "\n".join(chunks).lower()


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

    text = last_assistant_text(events)
    if not text or not is_russian_prose(text):
        return 0

    candidates = collect_candidates(text)
    if not candidates:
        return 0

    corpus = verified_corpus(events)
    unverified = sorted(c for c in candidates if c.lower() not in corpus)
    if not unverified:
        return 0

    reason = (
        "EXPLANATION PROTOCOL GATE BLOCKED YOUR RESPONSE.\n\n"
        "Your last message used these Latin terms, and NONE of them appears "
        "in any tool result, file Read, tool input, or user message in this "
        "session:\n"
        "  " + ", ".join(unverified[:15]) + "\n\n"
        "That is the signature of a coined term -- typically completing the "
        "missing half of a real pair (search-time -> index-time). Per "
        "~/.claude/CLAUDE.md -> 'Explanation Protocol', required action NOW:\n"
        "  1. Replace each term with a plain Russian phrase, which is the "
        "default: 'во время индексирования', not 'index-time'.\n"
        "  2. Keep the term ONLY if the user genuinely needs it (it appears "
        "in docs they will read, or will be spoken at an interview) -- and "
        "then verify its exact spelling in the source first, and introduce it "
        "with its Russian equivalent on first use.\n"
        "  3. A verified half of a pair does NOT verify the other half. "
        "Check each term separately, by its literal written form.\n\n"
        "Do NOT bypass this hook by dropping the backticks or the hyphen. "
        "The point is that the reader must understand the word."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
