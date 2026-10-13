---
feature: principles-ssot
bd_id: python-ai-skills-5io
date: 2026-10-13
status: approved
risk: medium
risk_justification: Text edits across ~12 skill/agent/instruction files plus one new advisory hook and its tests; additive or pointer-replacing, reversible, no schema, API or security surface.
evidence: strong
evidence_justification: Every copy and gap located in this session by grep/read with file:line (listed below); hook delivery pattern already proven in the repo (skill-finish-guard.sh matcher Skill, delegation-pool-nudge.sh additionalContext); user approved scope and design in chat.
open_questions: []
functional_requirements:
  - id: FR-1
    text: One file, _code-quality/principles.md, is the single source of truth for programming principles; KISS and YAGNI come first and every principle is stated as a detectable violation sign, not a slogan.
  - id: FR-2
    text: No other maintained file restates a principle definition; former copies (_code-quality/SKILL.md list, reference/quality-cascade.md tables, agents/py-quality.md top-5, best-research section 3, audit-loop Principles, commands/pipeline.md step 3, global CLAUDE.md code rules) become pointers.
  - id: FR-3
    text: Every code-producing or code-reviewing skill or agent in the repo points to principles.md (do-feature steps 2/4/7/9/11/12, grace-plan, grace-execute, grace-multiagent-execute, grace-reviewer, best-research, audit-loop, do-autopilot, py-quality, commands/pipeline).
  - id: FR-4
    text: Prompts sent to non-Anthropic models (do-feature/reviewer-prompt.md, audit-loop/reference/codex-prompt.md) receive the file content inlined through a placeholder, because those models do not read ~/.claude.
  - id: FR-5
    text: A PreToolUse hook on the Skill tool injects principles.md as additionalContext when a listed code-related skill is invoked, including superpowers skills that cannot be edited.
  - id: FR-6
    text: A test fails when a principle definition is restated outside principles.md or a listed consumer stops pointing to it; it runs in make test and in pre-commit on markdown changes.
  - id: FR-7
    text: do-feature checks excess code - Step 9 reverse traceability (every task, function and parameter traces to an FR or contract), Step 11 self-check treats code beyond the plan as a deviation, Step 12 reviewer has an Excess dimension and limits edge-case demands to system boundaries, Step 2 NFRs need a source or go to LATER.
non_functional_requirements:
  - id: NFR-1
    text: The hook is advisory - exit 0 always, silent for unlisted skills, missing file or malformed input degrades to silence.
  - id: NFR-2
    text: principles.md stays short enough to inject on every listed Skill call (target 70 lines or fewer).
  - id: NFR-3
    text: make test green; settings.json.template stays valid JSON.
constraints:
  - superpowers plugin files are not edited (plugin cache, overwritten on update) - the hook reaches them instead.
  - _code-quality has context fork / agent Explore, so consumers read the file instead of invoking the skill.
---

# Discovery: single source of truth for programming principles (python-ai-skills-5io)

Intent: the user sees too much redundant code from the pipelines and wants KISS and YAGNI
enforced strictly, with one authoritative principles file used by every relevant skill.

Facts found in this session:

1. Principle lists exist in `_code-quality/SKILL.md:17-41`, `_code-quality/reference/quality-cascade.md`,
   `agents/py-quality.md:13-18`, `best-research/SKILL.md:46-53`, `audit-loop/SKILL.md:367-377`,
   `audit-loop/reference/codex-prompt.md:24`, `commands/pipeline.md:144-148` and the global
   `claude-home/CLAUDE.md` Preferences. They already diverge: a KISS violation is a "blocker" in
   `_code-quality` and "critical" in `audit-loop`; `audit-loop` adds SOTA, absent elsewhere.
2. `do-feature` never mentions KISS or YAGNI. Step 9 checks coverage one way only ("Every FR →
   covered by task"); `reviewer-prompt.md` has no excess-code dimension and its item 1 asks for
   broad edge-case handling; Step 11 self-check checks write scope (files), not code volume.
3. The superpowers excess check (`subagent-driven-development/task-reviewer-prompt.md:84`,
   "Extra: features that weren't requested") never runs in `do-feature`, whose Step 11 uses
   `grace-execute`.
4. `_code-quality` frontmatter has `context: fork`, `agent: Explore` - invoking it starts a subagent.

Scope: IN - FR-1..FR-7. OUT - mechanical dead-code tooling (vulture) in project templates.
LATER - the same tooling as a pre-commit gate for dev projects, after a Context7 check.
