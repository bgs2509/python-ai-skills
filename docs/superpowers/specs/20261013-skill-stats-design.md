---
feature: skill-stats
bd_id: python-ai-skills-8of.1
date: 2026-10-13
status: approved
risk: low
open_questions: []
context7_verified: []
---

# Design: skill-stats (python-ai-skills-8of.1)

No third-party libraries (stdlib only) — `context7_verified` is empty on purpose.

- D-1 File `claude-home/scripts/skill-stats.py`, sibling of `model-stats.py`, same shape: module
  docstring with usage, `summarize()` pure function over parsed events, `render()` /
  `--json`, `main()`. Rejected: extending `model-stats.py` (different input — model-run journal vs
  transcripts; one tool per question).
- D-2 Parsing: `scan(path)` yields events `skill`, `human`, `usage` (with model, four token
  fields, 5m/1h cache-write split). Human message = user record, not `isMeta`, no `tool_result`,
  text not starting with `<`, `Base directory for this skill`, `[Request interrupted`, `Caveat:`.
  `/command` from `<command-name>`; `BUILTINS` set excluded; `/clear` closes windows.
- D-3 Attribution as the prototype: two accumulators (low/high); per-invocation low-bound totals
  kept in a list for median/p90 (nearest-rank, same helper style as `model-stats.py`).
- D-4 Prices: `PRICES` dict keyed by API model id → (input, 5m write, 1h write, cache read,
  output) $/MTok, source `platform.claude.com/docs/en/about-claude/pricing`, read 2026-10-13.
  Haiku 5.5 priced at the ≤100 k-prompt tier, and prompts above 100 k at the higher tier
  (input+cache tokens of the request decide). Unknown model → tokens counted under
  `unpriced_tokens`, cost 0.
- D-5 First-request context: input + cache read + cache write of the first deduplicated API
  response of each main transcript and each subagent transcript; median and p90.
- D-6 `--since DAYS` filters by event timestamp; `--top N` limits text rows (JSON has all).
- D-7 Template: `"cleanupPeriodDays": 180`.
- D-8 Tests `claude-home/scripts/test_skill_stats.py` on synthetic JSONL in `tmp_path`: window
  low/high, `/clear`, builtin excluded, dedup, subagent attribution + model mix, cost incl. Haiku
  tier switch, unpriced model, median/p90, first-request size, invalid line skipped, `--since`,
  CLI `--json` smoke; template test asserts 180.
