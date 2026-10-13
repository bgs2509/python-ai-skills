---
feature: subagent-models
bd_id: python-ai-skills-8of.4
date: 2026-10-13
status: approved
risk: medium
open_questions: []
context7_verified: []
---

# Design: subagent model routing (python-ai-skills-8of.4)

No third-party libraries — `context7_verified` is empty on purpose.

- D-1 Template `env`: `"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"`. Rejected: `haiku` as default
  (launches without a model include code changes and research writing, plan §3d); `_FORCE`
  (would override do-feature's Fable/Haiku tier choices).
- D-2 Registry top-level block `agent_work_types`: ordered list of
  `{"work": <text>, "tier": <tier>}` or `{"work": <text>, "role": <role>}` plus `_comment`.
  Entries: discovery, architecture, contracts and plan audits → `top`; writing code, tests and
  docs, decision records → `mid`; read-only exploration, search, inventories, log/transcript
  digests, mechanical reformatting → `cheap`; code review → role `reviewer`; web research with
  sources → role `researcher`. `version` 2, `updated` 2026-10-13.
- D-3 Hook: a second python block decides the model hint from `tool_input.model`,
  `subagent_type`. No hint when `model` is set or `subagent_type == "fork"`. Otherwise read
  `$MODEL_REGISTRY` (default `~/.claude/model-registry.json`), resolve each tier through
  `tiers` → `models[*].model_arg`, render one line per entry ("<work> → `model: <alias>`" or
  "→ `model-run.sh --role <role>`"). For `Explore` prepend that it runs on the session model
  unless `model` is passed. Registry missing/unreadable → generic hint without the list.
  Bulk nudge text unchanged; when both fire, texts are joined with a blank line.
- D-4 Registry `models.haiku`: `context_tokens` 1000000, notes: alias resolves to
  claude-haiku-5-5 (verified 2026-10-13), price ×5 above 100k-token prompts, A/B 4/4 on
  read-only tasks at 15-23× lower cost than Sonnet 5.5; `measured_seconds` kept (historical).
- D-5 `do-feature/SKILL.md` lines 95 and 126: window text says every current tier holds 1M;
  the cheap tier's constraint is price above 100k-token prompts, not a window.
- D-6 Tests: hook — model hint present without model, absent with model, absent for fork,
  Explore wording, mapping rendered from a synthetic registry (tier → alias, role → runner),
  broken registry path → generic hint, bulk+model hints combined, existing tests unchanged.
  Registry — `agent_work_types` tiers/roles exist in `tiers`/`roles`; haiku window 1M.
  Template — env key equals `sonnet`.
