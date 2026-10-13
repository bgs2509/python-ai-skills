---
feature: skill-listing
bd_id: python-ai-skills-8of.3
date: 2026-10-13
status: approved
risk: low
open_questions: []
context7_verified: []
---

# Design: skill listing (python-ai-skills-8of.3)

- D-1 `settings.json.template`: `skillOverrides` with `"name-only"` for the 30 never-invoked repo skills
  (list from `skill-stats.py --json`, 2026-10-13). Rejected: `disable-model-invocation` in each SKILL.md
  (hides the skill from the model entirely — orchestrators call `grace-*` by name); `off` (removes from `/`).
- D-2 Test: template keys are existing repo skill directories and every value is `name-only`.
- D-3 Verify: `claude -p "/context"` Skills line before (10k) and after.
- D-4 Revisit after 90 days with `skill-stats.py`: a skill invoked again by name stays name-only unless
  routing misses are observed.
