# ADR-003: External code review in do-feature Step 12

## Task
python-ai-skills-xp4

## Status
Accepted (2026-09-24). Supersedes the Step 12 part of ADR-002 (strong-tier Anthropic reviewer); the rest of ADR-002 stands.

## Context
User requirement (2026-09-24): plans and designs are written by Anthropic models, the code review is done by GLM or GPT, and the reviewer receives an exhaustive prompt stating what to check and what result to return. Until now Step 12 dispatched an Anthropic subagent (`Agent(model=<strong>)`), and the outward-dispatch fork listed review as Anthropic-only judgement because external review quality was unmeasured.

## Evidence (measured 2026-09-24, one range)
Same range (`ddf0dc6^..d8f81aa`, bd python-ai-skills-2fu, 8 commits), same 36-line prompt, reviewers run in a detached worktree at the reviewed commit. Baseline: the Anthropic Step 12 review of that range, 9 findings in ~3 min.

| Reviewer | Time | Anthropic findings recovered | Extra real defects (verified) | Notes |
|---|---|---|---|---|
| gpt-sol-xhigh (codex, read-only) | 558 s | 8 of 9 | 2 (`--out --dry-run` ran the model; `--expect ''` disabled the check) — fixed in python-ai-skills-luz | answered in Russian though asked English; 327 KB log around the report |
| glm-5.3-high (claude-glm) | 533 s | 6 of 9 | 0 verified (2 minor, unverified) | missed interrupt handling, docs-only policy, one design-friction item |

Neither external reviewer modified the worktree. Full notes: bd comments on python-ai-skills-xp4.

## Considered Alternatives
1. Keep the Anthropic strong-tier reviewer — rejected: contradicts the user requirement; the measured external recall is comparable.
2. Two external reviewers in parallel, merged — rejected by the user (DQ-1): the union added two minor items for twice the external quota.
3. Stop and ask when both externals fail — rejected by the user (DQ-2): a feature must not stall at Step 12 over an exhausted quota.

## Decision
1. Registry role `reviewer` = `gpt-sol-xhigh` → `glm-5.3-high` → `opus-xhigh`, role timeout 1800 s; first valid review wins. Using opus is a logged routing exception.
2. The reviewer prompt is the versioned template `do-feature/reviewer-prompt.md`; the answer must end with a verdict line checked by `--expect '^(READY|READY WITH FIXES|NOT READY)$'`.
3. The reviewer runs in a temporary detached worktree, removed afterwards (DQ-3).
4. `model-run.sh` gives every attempt an answer file (`MODEL_RUN_ANSWER_FILE`); codex writes its final message there (`-o`), so the delivered review is the report, not the log.
5. Trust = 0% is unchanged: the orchestrator verifies every finding before acting.

## Consequences
- Review leaves the Anthropic pool: the scarce quota is spent on plans and designs, as intended.
- Step 12 latency grows from ~3 min to ~9-10 min per feature (run in the background).
- Evidence is one range. Revisit after the first five Step 12 reviews under this ADR: compare what the external review found against defects found later; if recall drops, reconsider parallel reviewers or reordering.
