# Round summary block (after gate)

Projection of `state.json` — no duplication.

```
═══ R{N}/5 SUMMARY ═══
Found this round: <total> (<C>c / <M>m / <Min>min)
  ↻ repeated from R{N-1}: <count> (<c>c / <m>m / <min>min)
  ✦ new: <count>

Fixed this round: <count>
  AUTO (≥70% confidence): <count> → commits <sha1>, <sha2>, ...
  ASKED (<70%, batch /qa): <count> → user decisions logged in round-{N}.md

Deferred / documented: <count> → <ADR-NNN list>
Still open: <count> (<list of issue-ids with module_id and kind>)

Trend (critical / medium / minor across rounds):
  R1: <c> / <m> / <min>
  ...
  R{N}: <c> / <m> / <min>   ← stagnation triggered (if applicable)

Cycle metrics:
  median time per finding: <Ns>
  auto/asked/deferred ratio: <A%/B%/C%>
  top-3 stagnation modules: <M-X>, <M-Y>, <M-Z>

Hooks: pre-commit <✓/✗> · grace-refresh <✓/✗> · grace lint <✓/✗>
Time: <M>m<S>s · Next: R{N+1} (or /audit-loop --finish)

📄 Full details: docs/audit-loop/round-{N}.md
```

**Rules:**
- **Repeated** = same `(module_id, category, kind)` key as in R{N-1}. Either an unfixed-fix or regression.
- **New** = key absent in R{N-1}. R1 has repeated=0 by definition.
- **Still open** = not fixed, not deferred this round → carries to R{N+1}.
- Trend built from `state.json.rounds[*].codex_summary`. Cycle metrics computed cumulatively.
