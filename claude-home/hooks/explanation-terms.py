#!/usr/bin/env python3
"""Explanation-terms Stop hook.

Reads Stop event JSON from stdin, scans the final assistant message
(`last_assistant_message`) for Latin-script coined terms inside Russian prose,
and asks for a one-line correction per term if such a term never appears in
tool results, tool inputs or user messages of the current session, in the
user's standing instruction files (global and project CLAUDE.md/AGENTS.md,
installed skill/agent names), or in the files of the current git repository.

Two candidate shapes are checked, on whole whitespace-separated words:
  1. hyphenated Latin compounds  -- index-time, write-through
  2. single Latin words in inline backticks  -- `boosting`, `analyzer`
Words with `_`, digits or `/`, and single backticked words with a capital
after the first letter (`HTTPServer`, `HTTPS`, camelCase), are identifiers,
not coined terms, and are skipped. A compound keeps capitals inside:
`reverse-WireGuard` is coined.

Rationale: a term the model actually read somewhere leaves a trace in the
session or the repository. A term the model constructed on the fly --
typically by completing the missing half of a real pair, as in
search-time -> index-time -- leaves no trace at all.

The hook never blocks: the user has already read the message, and a block made
the model rewrite it (bd python-ai-skills-r1f.1: 106 blocks in 76 sessions,
answered with repeats and out-of-context paragraphs). Stop `additionalContext`
asks instead for exactly one line per term, saying which word is replaced by
which, or that the word is real.

Deliberately NOT detected: Russian jargon ("прогон" instead of
"тестирование"). It is formally indistinguishable from any other Russian
word, so it stays on the rule in CLAUDE.md rather than on this hook.

See ~/.claude/CLAUDE.md -> "Explanation Protocol".
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

import glossary


def log_block(detail: dict) -> None:
    """Append one JSONL record to the hook journal for monthly review."""
    try:
        log_dir = pathlib.Path.home() / ".claude" / "hook-stats"
        log_dir.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "hook": "explanation-terms",
            "cwd": os.getcwd(),
            **detail,
        }
        with open(log_dir / "blocks.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass

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

COMPOUND = re.compile(r"[A-Za-z]{2,}(?:-[A-Za-z]{2,})+")
SINGLE_WORD = re.compile(r"[A-Za-z][a-z]{4,}")
# Punctuation that may stick to a word in prose; stripped before shape checks.
WORD_EDGES = ".,;:!?()[]{}«»\"'*`"
# One git grep for all words; the Stop hook itself has 10 s in settings.json.template.
GIT_GREP_TIMEOUT_S = 5


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

    # Shape 1: a whole word that is a hyphenated Latin compound.
    for word in prose.split():
        word = word.strip(WORD_EDGES)
        if len(word) >= 6 and COMPOUND.fullmatch(word):
            candidates.add(word)

    # Shape 2: single Latin word inside inline backticks.
    for m in re.findall(r"`([^`\n]{1,40})`", prose):
        token = m.strip()
        if SINGLE_WORD.fullmatch(token):
            candidates.add(token)

    return {c for c in candidates if c.lower() not in IGNORE}


def instruction_corpus(cwd: str) -> str:
    """Standing instruction files and installed skill/agent names.

    Vocabulary the user wrote into their own global/project rules
    (do-feature, knowledge-graph, Fail-Fast, ...) is not a coined term, but
    system instructions never appear in the transcript as tool results, so
    without this the hook flags the model for quoting the user's own rules.
    """
    home = pathlib.Path.home() / ".claude"
    files = [home / "CLAUDE.md", home / "CLAUDE-APPENDIX.md"]
    for d in (home / "output-styles",):
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))
    if cwd:
        for name in ("CLAUDE.md", "AGENTS.md"):
            files.append(pathlib.Path(cwd) / name)
    chunks = []
    for f in files:
        try:
            if f.is_file():
                chunks.append(f.read_text(errors="ignore")[:100_000])
        except OSError:
            continue
    # Skill and agent names are installed vocabulary even when no
    # instruction file spells them out.
    for d in (home / "skills", home / "agents"):
        try:
            if d.is_dir():
                chunks.extend(p.name for p in d.iterdir())
        except OSError:
            continue
    return "\n".join(chunks)


def session_corpus(transcript_path: str) -> list:
    """Tool results, tool inputs and user messages of the session, one fragment each."""
    p = pathlib.Path(transcript_path) if transcript_path else None
    if not p or not p.is_file():
        return []
    try:
        lines = p.read_text(errors="ignore").splitlines()
    except OSError:
        return []
    chunks = []
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
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
    return chunks


def normalise(fragment: str) -> str:
    """Join words a terminal wrapped after a hyphen; collapse other whitespace."""
    fragment = re.sub(r"-[ \t]*\n\s*", "-", fragment)
    return re.sub(r"\s+", " ", fragment).lower()


def repository_mentions(words: list, cwd: str) -> set:
    """The words (lowercased) that some file tracked by the git repository at cwd mentions."""
    if not cwd or not words:
        return set()
    patterns = [arg for w in words for arg in ("-e", w)]
    try:
        r = subprocess.run(
            # -o -h prints each matched text alone; ':/' searches from the repository root.
            ["git", "-C", cwd, "grep", "-F", "-i", "-o", "-h", "-I", *patterns, "--", ":/"],
            capture_output=True,
            text=True,
            timeout=GIT_GREP_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return {line.lower() for line in r.stdout.splitlines()}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    if data.get("stop_hook_active"):
        return 0

    text = data.get("last_assistant_message") or ""
    if not is_russian_prose(text):
        return 0

    candidates = collect_candidates(text)
    try:
        candidates -= glossary.forbidden_latin_forms(data.get("cwd") or "")
    except Exception:  # a glossary problem never silences the coined-term check
        pass
    if not candidates:
        return 0

    cwd = data.get("cwd") or ""
    fragments = session_corpus(data.get("transcript_path")) + [instruction_corpus(cwd)]
    # Fragments stay apart, so a wrap join never glues the end of one to the start of another.
    corpus = "\n".join(normalise(f) for f in fragments)
    unseen = sorted(c for c in candidates if c.lower() not in corpus)
    in_repo = repository_mentions(unseen, cwd)
    unverified = [c for c in unseen if c.lower() not in in_repo]
    if not unverified:
        return 0

    words = ", ".join(f"«{w}»" for w in unverified)
    context = (
        "EXPLANATION PROTOCOL: these Latin words in your last message appear in no "
        "tool result, tool input or user message of this session, in no instruction "
        f"file and in no file of the repository: {words}.\n\n"
        "The user has ALREADY READ that message. Do NOT repeat, rewrite or quote it; "
        "no paragraphs, no 'проверяю', no apology. Reply with exactly one line per word "
        "and nothing else, in one of two forms:\n"
        "  Поправка к термину: «<word>» → «<plain Russian description of what it means>»\n"
        "  «<word>» — <where it occurs or what it is>, замены нет\n"
        "Use the second form only for a real name or an established industry term. "
        "See ~/.claude/CLAUDE.md -> 'Explanation Protocol'."
    )
    log_block({"unverified": unverified})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": context,
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
