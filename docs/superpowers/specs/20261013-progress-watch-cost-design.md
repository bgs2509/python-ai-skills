---
feature: progress-watch-cost
bd_id: python-ai-skills-8of.2
date: 2026-10-13
status: approved
risk: low
open_questions: []
context7_verified: []
---

# Design: progress-watch cost (python-ai-skills-8of.2)

- D-1 Phase 0 gets a first step "Choose the session": one check costs two requests over this session's
  whole context (measured numbers quoted). For file / PID / CI / GPU targets say so in one line and offer
  `claude --model haiku` + `/progress-watch <target> --every <N>` in a fresh session; continue here when
  the user prefers or the target is a subagent (TaskList is session-bound).
- D-2 Cron prompt becomes plain text: `progress-watch check pw-<slug>` + state + one combined probe
  command + the four-line rules + stop rules + the three never-rules. It must say not to invoke the skill.
- D-3 Phase 1: probe and liveness joined in one wrapped Bash call.
- D-4 `--iteration` stays accepted for jobs created before the change (old prompts keep working).
- D-5 Verification: read-through against hard rules and whitelist; `--once` flow unchanged; re-measure
  2026-10-20.
