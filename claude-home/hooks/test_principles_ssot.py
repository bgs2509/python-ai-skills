"""Guard for the single source of truth of the code principles (bd python-ai-skills-5io).

_code-quality/principles.md is the only place a principle is defined. Before it
existed the list was restated in seven files and the copies diverged (a KISS
violation was a "blocker" in one and "critical" in another). This guard fails when
a definition reappears elsewhere, when a consumer stops pointing to the file, or
when the hook's skill list names a repo skill that does not exist.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SSOT = REPO / "_code-quality" / "principles.md"
HOOK = REPO / "claude-home" / "hooks" / "principles-inject.sh"

NAMES = (
    r"SSoT / DRY|KISS|YAGNI|DRY|SSoT|SOTA|SoC|CoC|SRP|OCP|LSP|ISP|DIP|LoD|Fail Fast|Security|Testability"
    r"|Explicit > Implicit|Composition > Inheritance"
)
DEFINITION = re.compile(
    rf"\*\*({NAMES})\*\*\s*[—–-]"  # "**KISS** — ..."
    # Numbered table row "| 2 | **KISS** | ..."; the number column keeps NFR category
    # tables ("| **Security** | Authentication, ...") from matching.
    rf"|^\|\s*\d+\s*\|\s*\*\*({NAMES})\*\*\s*\|"
    rf"|\b(KISS|SRP)\s*\(\s*(≤|<=|<|>)"  # "KISS (≤50 lines ..."
    rf"|\|\s*(≤|<=|<|>)[^|\n]*\|\s*({NAMES})\s*\|",  # "| Function length | ≤ 50 lines | KISS |"
    re.M,
)
# Historical records and research are not maintained instructions.
SKIP_DIRS = {"docs", "reports", "research_notes", ".beads", ".claude", ".codex", ".git", ".worktrees"}
SKIP_FILES = {"CHANGELOG.md"}

# Consumer file -> text that proves it is wired to the SSoT.
CONSUMERS = {
    "_code-quality/SKILL.md": "principles.md",
    "agents/py-test-writer.md": "principles.md",
    "_testing/SKILL.md": "principles.md",
    "agents/py-quality.md": "principles.md",
    "best-research/SKILL.md": "principles.md",
    "audit-loop/SKILL.md": "principles.md",
    "audit-loop/reference/codex-prompt.md": "${PRINCIPLES}",
    "commands/pipeline.md": "principles.md",
    "do-autopilot/SKILL.md": "principles.md",
    "do-feature/SKILL.md": "principles.md",
    "do-feature/reference.md": "principles.md",
    "do-feature/reviewer-prompt.md": "{PRINCIPLES}",
    "grace-plan/SKILL.md": "principles.md",
    "grace-execute/SKILL.md": "principles.md",
    "grace-multiagent-execute/SKILL.md": "principles.md",
    "grace-reviewer/SKILL.md": "principles.md",
    "claude-home/CLAUDE.md": "principles.md",
}


def maintained_markdown():
    for path in REPO.rglob("*.md"):
        rel = path.relative_to(REPO)
        if rel.parts[0] in SKIP_DIRS or rel.name in SKIP_FILES or path == SSOT:
            continue
        yield rel, path


@pytest.mark.parametrize(
    "line",
    [
        "1. **KISS** — simplest code",
        "**SSoT / DRY** — every fact has one home",
        "**Security** - no secrets",
        "**Explicit > Implicit** — type hints",
        "**Composition > Inheritance** – is-a only",
        "| 2 | **YAGNI** | only what is needed |",
        "| 17 | **Testability** | injected |",
        "KISS (≤50 lines)",
        "| Function length | ≤ 50 lines | KISS |",
    ],
)
def test_definition_pattern_catches_restatements(line):
    assert DEFINITION.search(line)


def test_nfr_category_table_is_not_a_definition():
    assert not DEFINITION.search("| **Security** | Authentication, authorization, encryption |")


def test_every_principle_label_in_ssot_is_guarded():
    labels = re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", SSOT.read_text(), re.M)
    assert len(labels) == 17
    assert [x for x in labels if not re.fullmatch(NAMES, x)] == []


def test_ssot_file_stays_short_enough_to_inject():
    assert len(SSOT.read_text().splitlines()) <= 70


def test_codex_prompt_body_has_no_backticks():
    # audit-loop passes the prompt through an unquoted heredoc so ${N} and
    # ${PRINCIPLES} expand; a backtick in the body would run as a command.
    text = (REPO / "audit-loop" / "reference" / "codex-prompt.md").read_text()
    body = text.split("```", 2)[1]
    assert "`" not in body and "$(" not in body


def test_ssot_file_exists_and_puts_kiss_yagni_first():
    text = SSOT.read_text()
    found = [m.group(1) for m in re.finditer(rf"\*\*({NAMES})\*\*", text)]
    assert found[:2] == ["KISS", "YAGNI"]


def test_no_principle_definition_outside_ssot():
    hits = [
        f"{rel}:{text.count(chr(10), 0, m.start()) + 1}: {m.group(0)}"
        for rel, path in maintained_markdown()
        for text in [path.read_text(errors="ignore")]
        for m in DEFINITION.finditer(text)
    ]
    assert hits == [], "principle restated outside _code-quality/principles.md:\n" + "\n".join(hits)


def test_every_consumer_points_to_ssot():
    missing = [rel for rel, marker in CONSUMERS.items() if marker not in (REPO / rel).read_text()]
    assert missing == []


def test_hook_lists_only_existing_repo_skills():
    block = re.search(r"^SKILLS=\((.*?)^\)", HOOK.read_text(), re.S | re.M).group(1)
    names = block.split()
    assert names, "empty skill list"
    # Repo skills are dirs with SKILL.md; commands/<name>.md is invoked through the Skill tool too.
    repo_skills = [
        n
        for n in names
        if ":" not in n and not (REPO / n / "SKILL.md").exists() and not (REPO / "commands" / f"{n}.md").exists()
    ]
    allowed_external = {"simplify", "code-review"}  # built-in Claude Code skills
    assert [n for n in repo_skills if n not in allowed_external] == []
