---
feature: skill-listing
bd_id: python-ai-skills-8of.3
date: 2026-10-13
status: approved
risk: low
risk_justification: One settings key (skillOverrides) in settings.json.template; reversible by deleting the key; no code, no API, no security surface.
evidence: strong
evidence_justification: skill-stats.py over 35 days of transcripts (30 repo skills with zero model and zero slash invocations); /context breakdown of a fresh session (Skills 10k tokens); skillOverrides semantics quoted from code.claude.com/docs/en/skills ("name-only" = listed by name only, still in the / menu).
open_questions: []
functional_requirements:
  - id: FR-1
    text: Repo skills with no invocation in the measured period are listed to the model by name only (skillOverrides name-only); invoked skills keep their descriptions.
  - id: FR-2
    text: The skill listing in a fresh session shrinks, measured with /context before and after.
non_functional_requirements:
  - id: NFR-1
    text: Every skill stays invocable by name and from the / menu; make test green; template stays valid JSON.
constraints:
  - Plugin skills are not affected by skillOverrides (docs) and are out of scope.
---

# Discovery: skill listing (python-ai-skills-8of.3, plan item 2f)

`/context` in a fresh session of this repo: Skills 10k tokens of ~43k. `skill-stats.py` (2026-09-09..10-13):
30 of 47 repo skills were never invoked, among them `do-autopilot` and `do-multiagent` with descriptions
over 1,000 characters each. Their descriptions are paid on every request and bought nothing in the period.
