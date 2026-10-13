---
feature: best-research-cost
bd_id: python-ai-skills-8of.7
date: 2026-10-13
status: approved
risk: low
risk_justification: Text of best-research/SKILL.md plus one clause of the global Tooling Preferences line; reversible; no code.
evidence: strong
evidence_justification: Tool calls inside best-* windows counted from transcripts - best-approach 31 calls with 83 sequential-thinking calls and 21 ToolSearch loads, 168 Bash; best-questions median 5 requests per call at 330k context, best-approach 10 at 155k; every host tool call re-reads the session context.
open_questions: []
functional_requirements:
  - id: FR-1
    text: best-research reasons with built-in thinking and does not call sequential-thinking.
  - id: FR-2
    text: best-research does not re-read CLAUDE.md files (already in context) and delegates code study needing more than three reads/searches to one Explore subagent with model haiku returning a file:line digest, spot-checked by the parent.
  - id: FR-3
    text: best-research no longer allows tables in the terminal, matching the global Output Formatting rule.
  - id: FR-4
    text: Global Tooling Preferences calls sequential-thinking only when a skill or the user asks for it.
non_functional_requirements:
  - id: NFR-1
    text: Re-measure after 7 days - requests per best-approach / best-questions call (skill-stats.py).
constraints:
  - do-autopilot and audit-loop keep their explicit sequential-thinking steps (a skill asking for it).
---

# Discovery: best-* cost (python-ai-skills-8of.7, revision plan step 6)

Per-call profile: best-questions 5 requests (median) at 330k context, best-approach 10 at 155k. In
best-approach windows sequential-thinking was 23 % of all tool calls, each one a request over the whole
session context; Bash reads were another 46 %.
