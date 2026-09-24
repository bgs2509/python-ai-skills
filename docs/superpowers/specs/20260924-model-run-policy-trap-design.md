---
feature: model-run-policy-trap
bd_id: python-ai-skills-xwa
date: 2026-09-24
status: approved
risk: low
open_questions: []
context7_verified: []
---

# Design: model-run policy and interrupt handling (python-ai-skills-xwa)

No third-party libraries (bash, jq, coreutils) — `context7_verified` is empty on purpose.

## D-1 Penalty policy (FR-1, FR-2)

Chosen: the runner reads `policy.penalize_on` once at startup
(`jq -c '.policy.penalize_on // ["unavailable"]'`) and penalises an outcome that is in the list;
`timeout` additionally keeps the per-model `penalize_on_timeout` override. `no_penalty_on` is removed
from the registry.
Rejected: "declare the block descriptive" — keeps two lists that must be hand-synced with code
(SSoT violation, the defect itself). Rejected: keeping `no_penalty_on` next to `penalize_on` — it is
derivable, so a second source for the same fact.

## D-2 Interrupt (FR-3)

Chosen: run the attempt as a background job and `wait` for it, so a trapped INT/TERM is handled at
once. The trap (set only around an attempt) sends TERM to the `timeout` process (which forwards it to
the model command), journals `interrupted` with `out_path`/`out_bytes`, prints the kept path and exits
128+signal. Exit code of a normal attempt is `wait`'s status, identical to the old foreground status
(124 on timeout).
Rejected: delete the `.out` on interrupt — loses the evidence FR-3 of python-ai-skills-2fu keeps.
Rejected: trap without background+wait — bash defers the trap until the child exits (up to the
model timeout).

## Tests (synthetic registry)

1. `penalize_on` containing `check_failed` penalises a check_failed attempt (FR-1).
2. Registry without `penalize_on` still penalises `unavailable` (FR-1 default).
3. Shipped registry: `penalize_on == ["unavailable"]`, no `no_penalty_on` key (FR-2) — replaces the
   old list assertion.
4. SIGTERM during a `sleep 30` model: exit 143 within 5 s, one journal line `interrupted` whose
   `out_path` exists, the `sleep` child is gone (FR-3).
5. `--help` mentions `interrupted` and `penalize_on` (FR-4).
