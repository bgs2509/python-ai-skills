# Plan: single source of truth for programming principles

bd: python-ai-skills-5io · Discovery/Design: `docs/superpowers/specs/20261013-principles-ssot-*.md`

| # | Task | FR | Verify |
|---|------|----|--------|
| 1 | RED: `claude-home/hooks/test_principles_inject.py` + `test_principles_ssot.py` | FR-5, FR-6 | pytest fails (hook and principles.md absent, copies present) |
| 2 | `_code-quality/principles.md`; slim `_code-quality/SKILL.md`; delete `reference/quality-cascade.md` | FR-1, FR-2 | ssot test: definition check passes for `_code-quality` |
| 3 | `claude-home/hooks/principles-inject.sh`; register in `settings.json.template` (Skill entry) | FR-5 | inject tests green; template JSON valid |
| 4 | Pointers: py-quality, best-research, audit-loop (+ codex-prompt `${PRINCIPLES}`, version 2), commands/pipeline, do-autopilot, grace-plan, grace-execute, grace-multiagent-execute, grace-reviewer, global CLAUDE.md | FR-2, FR-3, FR-4 | ssot test green |
| 5 | do-feature: SKILL.md Step 7 line; reference.md Steps 2/4/7/9/11/12; reviewer-prompt.md `{PRINCIPLES}` + Excess | FR-4, FR-7 | ssot test green; grep shows placeholders filled in procedure |
| 6 | Makefile test target; pre-commit `principles-ssot`; CHANGELOG | FR-6 | `make test` green; `pre-commit run --all-files` green |
| 7 | `make install-symlinks` re-render; live hook smoke test | FR-5 | hook output on a sample payload via `~/.claude/hooks/` path |

Reverse traceability: every task names its FR; nothing outside FR-1..FR-7 is built.
