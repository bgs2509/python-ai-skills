# Per-round markdown report template — `docs/audit-loop/round-${N}.md`

```markdown
# Audit Loop — Round N

## Codex summary
critical: X | medium: Y | minor: Z
stagnation_with_prev: bool

## Auto-applied decisions (confidence ≥70%)
### <issue-id> [<fingerprint>]
- decision: <what>
- confidence: <NN%>
- breakdown: context7 +20, principles +20, precedent +20, graph +12, reversibility +10
- evidence: <links>
- commit: <sha>

## Asked decisions (batch-qa, confidence <70%)
### <issue-id> [<fingerprint>]
- options shown: [...]
- user chose: <option>
- rationale: <why>
- commit: <sha>

## Deferred / documented
### <issue-id> [<fingerprint>]
- reason: <why not fix>
- ADR: docs/adr/ADR-NNN-*.md (if created)

## Hooks state
- pre-commit: pass/fail (details)
- grace-refresh: pass/fail
- grace lint: pass/fail

## Context7 docs cited (DRY for next rounds)
- <library>@<version>: <inline excerpt>
```
