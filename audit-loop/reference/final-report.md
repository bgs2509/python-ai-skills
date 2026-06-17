# Final report template — `docs/reports/YYYYMMDD_audit-loop.md`

Produced on round 5 or `--finish`.

```markdown
# Audit Loop — Final Report

## Cycle metadata
- Started / ended: <ISO> / <ISO>
- Rounds: <n>
- Total findings: critical X / medium Y / minor Z
- Closed: ... | Open: ... | Documented (ADR): ...

## Per-round trend
(Plain list, not table — Telegram-friendly)
- R1: <c>c / <m>m / <min>min · stagnation: n/a
- R2: ...
- R5: ...

## Cycle metrics
- median time per finding
- auto / asked / deferred ratio
- top-3 stagnation modules
- top-3 repeated kinds
- Context7 libraries seen

## Why errors didn't end (if applicable)
Stagnation episode analysis from sequential-thinking trace.

## GRACE skills usage
- grace-fix: N invocations
- grace-refactor: N
- grace-refresh: N
- best-questions: N (batched)

## Hooks history
- pre-commit failures by round
- grace lint failures by round

## Auto-applied decisions for review (manual git revert if needed)
Full list of all ≥70% decisions with breakdown, fingerprint, and commit SHA.
User reviews, runs `git revert <sha>` if any decision turns out wrong.

To revert all commits sharing one fingerprint (e.g. fix that turned out wrong across rounds):
```bash
python3 ~/.claude/skills/audit-loop/lib/revert_finding.py <fingerprint>
```
Prints a `git revert` plan (newest-first) without executing — user confirms manually.

## Open issues — Beads creation
After printing the list, the skill prompts:
> Create N Beads issues automatically for these open findings? [y/N]

If yes — execute `bd create` for each open critical/medium with:
- title: short kind summary
- description: finding description + evidence + audit-loop reference
- type: bug, priority: 1 for critical, 2 for medium

If no — print ready-to-paste `bd create` commands instead.

## ADRs created in cycle
- docs/adr/ADR-NNN-*.md — list

## Recommendations
- next steps
- bug patterns worth preventing via lint/hook rules
```
