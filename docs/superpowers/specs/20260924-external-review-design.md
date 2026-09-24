---
feature: external-review
bd_id: python-ai-skills-xp4
date: 2026-09-24
status: approved
risk: medium
open_questions: []
decisions:
  - DQ-1 -> sequential reviewer role, gpt-sol-xhigh first, glm-5.3-high on failure (user, 2026-09-24)
  - DQ-2 -> Anthropic (opus-xhigh) automatically last, logged as a routing exception (user)
  - DQ-3 -> reviewer runs in a detached temporary worktree at HEAD, removed afterwards (user)
context7_verified: []
---

# Design: external code review in do-feature Step 12 (python-ai-skills-xp4)

No third-party libraries (bash, jq, codex/claude CLIs verified with --help in-session).

- D-1 Registry role `reviewer`: `["gpt-sol-xhigh", "glm-5.3-high", "opus-xhigh"]` (per DQ-1/DQ-2 recommendation), `timeout_seconds: 1800` (both externals needed ~9 min on an 8-commit range).
- D-2 Template `do-feature/reviewer-prompt.md`: the comparison prompt generalised with placeholders `{RANGE}`, `{DISCOVERY}`, `{DESIGN}`, `{PLAN}`, `{FILES}`; output format in English ending with `## Verdict` and one line `READY` | `READY WITH FIXES` | `NOT READY`.
- D-3 `--expect '^(READY|READY WITH FIXES|NOT READY)$'` — an anchored single-verdict line; the template shows the three values on one line joined by ` | `, so the regex does not match the task text (model-run.sh rejects that).
- D-4 Answer file: every attempt gets `MODEL_RUN_ANSWER_FILE` (a sibling of the capture file) in its environment. The codex runner passes `-o "$MODEL_RUN_ANSWER_FILE"`, so the agent's final message lands there. If that file is non-empty after exit 0, it is the answer (checked by the empty/`--expect` rules and delivered to `--out`); otherwise stdout is the answer, as today for claude-family runners. Text patterns for non-zero exits still read the full capture. Non-ok attempts keep the full capture (the log); the answer file is removed. Applies to every role that uses codex (NFR-1); `cmd_template` commands can use the same variable, which is how it is tested.
- D-5 Step 12 procedure (reference.md): orchestrator creates a detached worktree at HEAD (DQ-3), fills the template into a task file, runs `model-run.sh --role reviewer --task … --out … --expect …` from the worktree, removes the worktree, then verifies each finding (FR-5); grace-reviewer full-integrity and Sentrux postflight stay as they are.
- D-6 SKILL.md: outward fork point 1 drops "review" from Anthropic-only judgement and names Step 12 as outward via the reviewer role; per-step defaults become "Steps 2, 4, 7, 8 always inward; Step 12 outward (reviewer role)"; matrix row 12 = `model-run.sh --role reviewer` + template, fallback per registry.
- D-7 ADR-003 "External code review in do-feature Step 12": context (user requirement, comparison numbers), decision, consequences (latency ~9 min vs ~3, quota moves off Anthropic, one-range evidence — revisit after N reviews), supersedes the Step 12 part of ADR-002.
- D-8 Tests: codex runner command contains `-o` (dry-run); on ok the delivered answer is the last-message file content; on non-ok the kept output is the log; shipped registry has the reviewer role with timeout 1800.
