#!/usr/bin/env python3
"""Project glossary hook: one canonical term per group of forbidden synonyms (bd python-ai-skills-du5).

A project keeps a `## Glossary` section in its AGENTS.md (or one pointer line to a separate
file): one bullet per group, `- «forbidden», «forbidden» → **canonical** — definition`. One
module, three modes, one matcher:

  memo     UserPromptSubmit: send the glossary (or the groups the prompt touches) before the answer
  stop     Stop: ask for one line `Поправка к термину: «X» → «Y»` per forbidden form in the last answer
  --staged pre-commit: report forbidden forms in the changed lines of staged files, exit 1 on findings

memo and stop are advisory (exit 0 on every path, no `decision`, silent without a glossary);
--staged is a gate (exit 0 / 1 findings / 2 glossary unreadable). Stdlib only.
See ~/.claude/CLAUDE.md -> "Explanation Protocol".
"""
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

GLOSSARY_HEADING = "## Glossary"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")  # first that is a regular file at the project root
SECTION_MAX_LINES = 200  # section form above this -> separate file
MEMO_MAX_CHARS = 8_000  # a memo carries the section or the touched groups only up to this (hook cap: 10,000)
GIT_TIMEOUT_S = 5  # Stop has 10 s, UserPromptSubmit 3 s
JOURNAL = Path.home() / ".claude" / "hook-stats" / "blocks.jsonl"

ENTRY_RE = re.compile(
    r"^[-*] (?:(?P<forms>«[^»]+»(?:, «[^»]+»)*) → )?\*\*(?P<canonical>[^*]+)\*\*"
    r"(?: — (?P<definition>.*?))?(?: \((?P<kind>источник|English): (?P<source>[^)]+)\))?\s*$"
)
FORM_RE = re.compile(r"«([^»]+)»")
POINTER_RE = re.compile(r"^Glossary file: `([^`]+)`\s*$")
EXCEPTION_RE = re.compile(r"^[-*] Исключение: «([^»]+)» — источник: (\S.*)$")

CYRILLIC = re.compile(r"[а-яёА-ЯЁ]")


class GlossaryError(ValueError):
    """The glossary breaks the contract: a bullet matching no form, two headings, an unreadable pointer."""


@dataclass(frozen=True)
class Group:
    forms: tuple  # forbidden forms, verbatim; empty for a group kept for the memo only
    canonical: str
    line: str


@dataclass(frozen=True)
class Glossary:
    path: str
    groups: tuple
    exceptions: tuple  # phrases in which a forbidden form is legal
    lines: tuple  # the cut section, heading included
    pointed: bool  # the groups come from a separate file


def cut_section(text, label):
    """Lines of the `## Glossary` section, heading to the line before the next `#` line; None without the heading."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.rstrip() == GLOSSARY_HEADING]
    if not starts:
        return None
    if len(starts) > 1:
        raise GlossaryError(f"{label}: more than one '{GLOSSARY_HEADING}' heading")
    end = next((i for i in range(starts[0] + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    section = lines[starts[0]:end]
    while not section[-1].strip():
        section.pop()
    return tuple(section)


def parse_section(lines, label):
    """(groups, exceptions, pointer) of a cut section.

    Fenced lines and prose are skipped; a bullet that is neither an entry nor an exception raises GlossaryError.
    The pointer is the whole body: one `Glossary file: ...` line and nothing else."""
    body, fenced = [], False
    for number, line in enumerate(lines[1:], 2):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif line.strip() and not fenced:
            body.append((number, line))
    pointer = POINTER_RE.match(body[0][1]) if len(body) == 1 else None
    if pointer:
        return (), (), pointer.group(1)
    groups, exceptions = [], []
    for number, line in body:
        if not line.startswith(("- ", "* ")):
            continue
        exception, entry = EXCEPTION_RE.match(line), ENTRY_RE.match(line)
        if exception:
            exceptions.append(exception.group(1))
        elif entry:
            groups.append(Group(tuple(FORM_RE.findall(entry.group("forms") or "")), entry.group("canonical"), line))
        else:
            raise GlossaryError(f"{label}: section line {number}: bullet matches no glossary form: {line}")
    return tuple(groups), tuple(exceptions), None


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=GIT_TIMEOUT_S)


def project_root(cwd):
    """The git work tree of cwd, else cwd itself (a worktree resolves to its own root)."""
    try:
        result = git(cwd or ".", "rev-parse", "--show-toplevel")
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.decode().strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(cwd or ".")


def read_source(root, name, staged):
    """Text of a file: from the git index under `staged` (falling back to disk), else from disk; None if unreadable."""
    if staged:
        result = git(root, "show", f":{name}")
        if result.returncode == 0:
            return result.stdout.decode("utf-8", "replace")
    try:
        return (Path(root) / name).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_glossary(root, staged=False):
    """The glossary of the project at root; None when it has none; GlossaryError when it is unreadable."""
    for name in INSTRUCTION_FILES:
        text = read_source(root, name, staged)
        if text is not None:
            break
    else:
        return None
    label = str(Path(root) / name)
    section = cut_section(text, label)
    if section is None:
        return None
    groups, exceptions, pointer = parse_section(section, label)
    if pointer is None:
        return Glossary(label, groups, exceptions, section, False)
    target = str(Path(root) / pointer)
    pointed_text = read_source(root, pointer, staged)
    if pointed_text is None:
        raise GlossaryError(f"{label}: pointed file {target} is unreadable")
    section = cut_section(pointed_text, target)
    if section is None:
        raise GlossaryError(f"{target}: no '{GLOSSARY_HEADING}' heading")
    groups, exceptions, again = parse_section(section, target)
    if again:
        raise GlossaryError(f"{target}: a pointed glossary must not point further")
    return Glossary(target, groups, exceptions, section, True)
