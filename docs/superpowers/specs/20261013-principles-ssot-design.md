---
feature: principles-ssot
bd_id: python-ai-skills-5io
date: 2026-10-13
status: approved
risk: medium
open_questions: []
context7_verified: []
---

# Design: single source of truth for programming principles (python-ai-skills-5io)

No third-party libraries - `context7_verified` is empty on purpose.

- D-1 SSoT file `_code-quality/principles.md`. Order: KISS, YAGNI, SSoT/DRY, SOTA first, then the
  remaining principles one line each with detectable violation signs; an "Excess code" check
  (deletion test) and a precedence rule (KISS/YAGNI win over OCP/DIP/ISP: no abstraction without
  two real implementations today). Lives in an existing skill dir, so `make install-symlinks`
  already exposes it at `~/.claude/skills/_code-quality/principles.md` and `~/.codex/skills/...`.
  Rejected: a new top-level dir (new install path); the SKILL.md itself (forks into Explore,
  carries frontmatter noise into injected text).
- D-2 Remove copies. `_code-quality/SKILL.md` keeps frontmatter, a pointer, the centralization
  table and the topic map (moved from quality-cascade.md). `reference/quality-cascade.md` is
  deleted - its tables are merged into principles.md. py-quality, best-research, audit-loop,
  commands/pipeline and global CLAUDE.md replace their lists with a pointer; audit-loop maps any
  principles.md violation to `critical` instead of a per-principle severity list.
- D-3 External prompts. `reviewer-prompt.md` gains `{PRINCIPLES}` (filled with the file content by
  the Step 12 procedure) and item 8 "Excess"; item 1 limits edge-case demands to system boundaries.
  `codex-prompt.md` gains `${PRINCIPLES}` inside its heredoc; `codex_prompt_version` 1 → 2.
- D-4 do-feature text. Step 2 Phase 3: every NFR names its source or goes to LATER. Step 4: read
  principles.md, options scored KISS/YAGNI first. Step 7: check contracts against principles.md
  (read, do not invoke `_code-quality`). Step 9: reverse-traceability and no-excess checklist
  items. Step 11: packet carries the principles path; code beyond the plan's GREEN is a deviation.
- D-5 grace-plan, grace-execute, grace-multiagent-execute, grace-reviewer: one pointer line each,
  at the place where contracts are written, packets built, or review checklists run.
- D-6 Hook `claude-home/hooks/principles-inject.sh`, PreToolUse matcher `Skill`, added to the
  existing Skill entry of the template. Skill list lives only in the hook. File path
  `${PRINCIPLES_FILE:-$HOME/.claude/skills/_code-quality/principles.md}`. Listed skill + readable
  file → additionalContext with a one-line header and the file content; otherwise silence.
- D-7 Tests. `test_principles_inject.py` - listed skill injects content, unlisted silent, missing
  file silent, malformed input silent, plugin-prefixed names. `test_principles_ssot.py` - no
  bold-dash or table-row principle definition outside principles.md in maintained markdown;
  each consumer file contains `principles.md`; every repo skill in the hook list exists.
  Both in `make test`; the ssot test also as a pre-commit hook on `*.md`.
