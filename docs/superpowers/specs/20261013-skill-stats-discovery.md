---
feature: skill-stats
bd_id: python-ai-skills-8of.1
date: 2026-10-13
status: approved
risk: low
risk_justification: One new read-only script with its test file plus one key in settings.json.template; additive, reversible, no public API, no security surface.
evidence: strong
evidence_justification: Prototype run on 2.1 GB of real transcripts in this session (docs/research/skills-revision-plan-2026-10.md §1.2-1.3, §1.8); structure follows claude-home/scripts/model-stats.py:1-60; open_questions resolved.
open_questions: []
functional_requirements:
  - id: FR-1
    text: skill-stats.py reads Claude Code transcripts (~/.claude/projects/**/*.jsonl, overridable) and attributes each API response, deduplicated by (message.id, requestId), to the skill whose window is open.
  - id: FR-2
    text: A skill window opens at a Skill tool_use or a /command; it closes at the next human-typed message or next skill (low bound) or at the next skill or session end (high bound). Built-in commands are not skills; /clear closes every window.
  - id: FR-3
    text: Subagent transcripts are attributed to the skill open in the parent session at the subagent's first timestamp; their model mix is reported per skill.
  - id: FR-4
    text: Per skill - calls (tool and slash), sessions, tokens low/high, tokens without cache reads, output, subagent tokens, per-invocation median and p90 tokens (low bound), API-equivalent cost.
  - id: FR-5
    text: Totals - all tokens, cache-read share, API-equivalent cost by model split main/subagent, tokens of unpriced models; first-request context size of main sessions and subagents (median, p90).
  - id: FR-6
    text: CLI --projects PATH, --since DAYS, --top N, --json; a truncated or invalid JSONL line never breaks the report.
  - id: FR-7
    text: settings.json.template sets cleanupPeriodDays to 180.
non_functional_requirements:
  - id: NFR-1
    text: Python 3 standard library only; facts only - every number is counted from transcript lines, prices are the only external constant and carry their source and date.
  - id: NFR-2
    text: make test green; the script is collected by the scripts-regression-tests pre-commit hook.
constraints:
  - Read-only - never writes into ~/.claude/projects.
  - Advisor spend is out of scope (not present in transcript usage, plan item 4b).
---

# Discovery: skill-stats (python-ai-skills-8of.1)

Step 0 of `docs/research/skills-revision-plan-2026-10.md`. The prototype written in this session
(`/tmp/claude-1000/skill_usage.py`) answered the revision's first question in 14 s over 2,233
files, but lives in a temp directory and lacks per-invocation statistics, cost and the subagent
model mix that steps 1-7 need for before/after comparisons.

Measured facts the tool must reproduce: 13.94 B tokens over 2026-09-09..2026-10-13, 97 % cache
reads, ≈ $6,505 API-equivalent; `do-feature` 34 calls, `progress-watch` 145 slash firings;
fresh `claude -p` session baseline 66-67 k tokens.

Retention: `cleanupPeriodDays: 30` (claude-home/settings.json.template:3) deletes transcripts older
than 30 days, so a six-month revision is impossible. User asked for six months → 180.
