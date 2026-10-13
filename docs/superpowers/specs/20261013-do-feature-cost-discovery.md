---
feature: do-feature-cost
bd_id: python-ai-skills-8of.8
date: 2026-10-13
status: approved
risk: medium
risk_justification: Two text changes in the do-feature orchestrator used by every dev change - one routing row (Step 4 tier) and one advisory pre-dispatch step; reversible; no code.
evidence: strong
evidence_justification: 37 do-feature runs measured - median 19 orchestrator requests per run at 246k context (180k at the start), subagent mix sonnet 1436 / fable 631 / opus 485 calls; user decision 2026-10-13 "discovery and architecture only on Fable" recorded in the revision plan (3b).
open_questions: []
functional_requirements:
  - id: FR-1
    text: Step 4 Brainstorming routes to the top tier, matching the user's rule for discovery and architecture.
  - id: FR-2
    text: Pre-dispatch offers a fresh session once when the current one carries a long unrelated conversation.
non_functional_requirements:
  - id: NFR-1
    text: Re-measure after 7 days - orchestrator requests and context per run, subagent mix (skill-stats.py).
constraints:
  - Step 11 worker default stays mid until python-ai-skills-4f4 revalidates tiers (Haiku 5.5 passed small code tasks only).
---

# Discovery: do-feature cost (python-ai-skills-8of.8, revision plan step 7)

Orchestrator cost per run ≈ 19 requests × 246k tokens ≈ 4.7M before subagents; the session context at
the start (median 180k) is the multiplier. Per-stage attribution needs stage markers in transcripts —
not available; the subagent model mix per run is (skill-stats.py).
