# ADR-002: Model Routing Matrix — A/B Validation Evidence

## Task
python-ai-skills-7u9 (do-feature audit round 2)

## Status
Accepted

## Context
`do-feature` routes each workflow step to a model tier (opus / sonnet / haiku) via the
Model Routing Matrix in `do-feature/SKILL.md`. The matrix was originally justified by
inline A/B numbers embedded in the skill body. Those numbers are historical evidence,
not control logic — keeping them in SKILL.md added token ballast on every invocation
and let them silently go stale. This ADR is now the SSoT for that evidence; the skill
references it by name.

## Evidence (A/B validated 2026-05-13)
- **Overall matrix vs all-Opus baseline:** ~−50–60% cost and ~−30% wall-clock without
  quality loss on critical decisions or review coverage.
- **Execution workers (Step 11):** Sonnet 26.8k tokens vs Haiku 56.9k tokens on an
  identical atomic task — Haiku's price margin (~33%) is eaten by retries and verbosity,
  hence **default Sonnet, not Haiku**.
- **Review (Step 12):** Opus found ~2× more bugs than Sonnet on the same input and
  reliably caught GRACE convention violations, hence Opus for the review dispatch.
- **Discovery/Brainstorming (Steps 2, 4):** sequential-thinking insights measurably
  deeper on Opus (caregiver, liability, PII blind spots surfaced only there).

## Considered Alternatives
- **Keep A/B numbers inline in SKILL.md** — rejected: token ballast on every load;
  history belongs in an ADR (repo Documentation SSoT rules).
- **Drop the evidence entirely** — rejected: the matrix would become an unexplained
  assertion; future revalidation needs the baseline numbers.

## Decision
Move all A/B evidence out of `do-feature/SKILL.md` into this ADR. The skill's matrix
and escalation rule cite `ADR-002` instead of restating numbers.

## Consequences
- Easier: SKILL.md is lighter and load-bearing only; evidence has one home.
- Limitation: the A/B was run 2026-05-13 against the Opus/Sonnet/Haiku lineup and
  predates the Claude 5 family (Fable). The matrix has NOT been revalidated against
  Claude 5 models — this is a known follow-up (medium finding, audit round 2). Until
  revalidation, the matrix remains the SSoT for routing.
