---
feature: progress-watch-cost
bd_id: python-ai-skills-8of.2
date: 2026-10-13
status: approved
risk: low
risk_justification: Text of one utility skill (progress-watch/SKILL.md); reversible; no code, no API, no security surface; the watched process is untouched by design.
evidence: strong
evidence_justification: 145 firings measured from transcripts with skill-stats.py internals - median 2 API requests per firing, median 494k context per request (p90 777k), median 1.09M tokens per firing; SKILL.md is 9.2k chars and is re-injected by every /progress-watch --iteration slash call.
open_questions: []
functional_requirements:
  - id: FR-1
    text: At bootstrap the skill states what one check costs in this session and, for targets that do not need this session's TaskList (files, PIDs, CI runs, GPUs), offers the cheap form - watch from a fresh session on the cheap tier.
  - id: FR-2
    text: The scheduled re-entry is a compact plain prompt carrying state, probe and the report rules, not a /progress-watch slash call, so a firing does not re-inject the whole skill.
  - id: FR-3
    text: Probe and liveness run in one Bash call per firing.
non_functional_requirements:
  - id: NFR-1
    text: All read-only and self-termination guarantees stay as they are (hard rules, whitelist, marker-based CronDelete).
  - id: NFR-2
    text: Effect is re-measured after 7 days (skill-stats.py --since 7) and recorded in the revision plan.
constraints:
  - Reports must reach the session the user watches, so a firing cannot leave that session; the lever is which session runs the watch and how much each firing adds.
---

# Discovery: progress-watch cost (python-ai-skills-8of.2, revision plan step 1)

Baseline 2026-09-09..10-13: 145 firings in 10 sessions, 421-823 M tokens. Per firing: 2 requests
(median), each re-reading the host session's context (median 494k tokens), so ~1.1 M tokens per check.
The skill text itself is under 1 % of that; the host context is the cost.
