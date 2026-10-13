"""Guard for the single source of truth of the code principles (bd python-ai-skills-5io).

_code-quality/principles.md is the only place a principle is defined. Before it
existed the list was restated in seven files and the copies diverged (a KISS
violation was a "blocker" in one and "critical" in another). This guard fails when
a definition reappears elsewhere, when a consumer stops pointing to the file, or
when the hook's skill list names a repo skill that does not exist.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SSOT = REPO / "_code-quality" / "principles.md"
HOOK = REPO / "claude-home" / "hooks" / "principles-inject.sh"

NAMES = r"KISS|YAGNI|DRY|SSoT|SOTA|SoC|CoC|SRP|OCP|LSP|ISP|DIP|LoD|Fail Fast"
DEFINITION = re.compile(
    rf"\*\*({NAMES})\*\*\s*[—–-]"  # "**KISS** — ..."
    rf"|^\|\s*(\d+\s*\|\s*)?\*\*({NAMES})\*\*\s*\|"  # "| 2 | **KISS** | ..."
    rf"|\b(KISS|SRP)\s*\(\s*(≤|<=|<|>)",  # "KISS (≤50 lines ..."
    re.M,
)
# Historical records and research are not maintained instructions.
SKIP_DIRS = {"docs", "reports", "research_notes", ".beads", ".claude", ".codex", ".git", ".worktrees"}
SKIP_FILES = {"CHANGELOG.md"}

# Consumer file -> text that proves it is wired to the SSoT.
CONSUMERS = {
    "_code-quality/SKILL.md": "principles.md",
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
