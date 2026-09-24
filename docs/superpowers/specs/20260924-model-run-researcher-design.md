---
feature: model-run-researcher
bd_id: python-ai-skills-a67
date: 2026-09-24
status: approved
risk: medium
open_questions: []
context7_verified: []
---

# Design: web-research role (python-ai-skills-a67)

No third-party libraries (bash, jq) — `context7_verified` is empty on purpose.

- D-1 Role name `researcher`, models `["glm-5.3-high", "gpt-terra-high", "sonnet-low"]`, `timeout_seconds: 900`, purpose and order_rationale citing the task-57 measurements. Rejected: reordering `executor` (codegen/test work would pay 900 s waits and lose glm-4.7's quick answers on small tasks); raising glm-5.3-high's model timeout (leaks into `planner`).
- D-2 `model-run.sh` reads `ROLE_TIMEOUT=$(jq -r --arg r "$ROLE" '.roles[$r].timeout_seconds // empty')` once; per attempt `timeout_s=${ROLE_TIMEOUT:-<model timeout>}`. Validated like retention: positive integer or exit 2. Dry-run shows the effective timeout.
- D-3 Tests: role timeout overrides a shorter model timeout (model sleeps 2 s, model timeout 1, role timeout 5 -> ok); without role timeout the same model times out; invalid role timeout -> exit 2; shipped registry: researcher exists, order as D-1, timeout 900, every model has `capabilities.web_search` true.
- D-4 Docs: CLAUDE.md "choosing WHICH model" lists five roles; the delegating paragraph says web research uses `--role researcher`; `--help` header notes `roles.<role>.timeout_seconds`.
