---
feature: model-run-researcher
bd_id: python-ai-skills-a67
date: 2026-09-24
status: approved
risk: medium
risk_justification: Two modules (model-registry.json schema + model-run.sh) plus tests and CLAUDE.md; additive, no breaking change, no security surface.
evidence: strong
evidence_justification: Measured in this session on task-57 (stream-json traces and journal lines; see bd comments on python-ai-skills-v6z and -2fu); registry timeouts read from claude-home/model-registry.json; open_questions resolved.
open_questions: []
functional_requirements:
  - id: FR-1
    text: The registry has a role for web research whose models, in order, are glm-5.3-high, gpt-terra-high, sonnet-low.
  - id: FR-2
    text: A role may declare timeout_seconds; when present, model-run.sh uses it instead of each model's timeout_seconds for attempts made under that role; roles without it keep per-model timeouts.
  - id: FR-3
    text: The web-research role declares timeout_seconds 900.
  - id: FR-4
    text: Every model of the web-research role has capabilities.web_search true (checked by the shipped-registry test).
  - id: FR-5
    text: CLAUDE.md names the role and when to use it; --help mentions the role-level timeout.
non_functional_requirements:
  - id: NFR-1
    text: No new runtime dependency; existing roles behave exactly as before (same timeouts).
  - id: NFR-2
    text: make test green; FR-2 proven with the synthetic-registry fixture.
constraints:
  - The registry stays the single home for model and role parameters (CLAUDE.md "choosing WHICH model").
---

# Discovery: web-research role (python-ai-skills-a67)

Measured on task-57 (verify school No. 57 facts on its official site), 2026-09-24:

1. glm-4.7 (executor #1): timeout at 420 s three times, and at 900 s in a traced run (49 tool calls, 764 s model time).
2. glm-5.3-high: answered in 648 s with a level-1 card read through the site's content API; three of four spot-checked quotes verified with curl.
3. gpt-terra-high: 206 s and 463 s, card from sch57.ru found by web search; codex could not open 57.mskobr.ru.
4. sonnet-low: 148 s, almost empty card ("content is JS-rendered").

glm-5.3-high's model timeout is 420 s (`model-registry.json`), so a run like (2) is cut off under model-run.sh. Changing that model timeout would also slow the planner role, where glm-5.3-high is #2 — hence a role-level timeout.
