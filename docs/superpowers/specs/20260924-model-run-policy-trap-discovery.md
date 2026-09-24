---
feature: model-run-policy-trap
bd_id: python-ai-skills-xwa
related_bd_ids:
  - python-ai-skills-2fu
date: 2026-09-24
status: approved
risk: low
risk_justification: One script (model-run.sh) plus its registry policy block and tests; reversible, no public-API break, no security surface.
evidence: strong
evidence_justification: Both defects cited from the Step 12 review of python-ai-skills-2fu and verified in this session (grep shows no reader of no_penalty_on besides a test; bash defers traps until a foreground child exits).
open_questions: []
functional_requirements:
  - id: FR-1
    text: model-run.sh penalises an attempt when its outcome is listed in the registry's policy.penalize_on (default ["unavailable"] when absent), or when the outcome is timeout and the model sets penalize_on_timeout.
  - id: FR-2
    text: The registry no longer carries policy.no_penalty_on (it is the complement of penalize_on and was read by nothing); the policy comment states that penalize_on is read by the runner.
  - id: FR-3
    text: On SIGINT or SIGTERM during an attempt, model-run.sh stops the running model command, writes one journal line with outcome interrupted and the kept output's path and size, and exits 130 (INT) or 143 (TERM) without waiting for the model timeout.
  - id: FR-4
    text: --help lists the interrupted outcome and the policy.penalize_on behaviour.
non_functional_requirements:
  - id: NFR-1
    text: No new runtime dependency (bash, jq, coreutils).
  - id: NFR-2
    text: make test stays green; each FR is proven by a test using the synthetic-registry fixture.
constraints:
  - Journal stays append-only and additive; interrupted is a new outcome value that model-stats.py renders generically.
scope_later:
  - Timeout diagnosis of glm-4.7 is python-ai-skills-v6z, not this feature.
---

# Discovery: model-run policy and interrupt handling (python-ai-skills-xwa)

Lightened Discovery (risk low): both defects come from the Step 12 review of
python-ai-skills-2fu and were re-verified in this session.

1. `policy.no_penalty_on` / `policy.penalize_on` in `claude-home/model-registry.json` are read by no
   code: `grep` over the repo finds only `test_model_run.py:358`, which asserts the list, not the
   behaviour. Penalties are hardcoded in `model-run.sh` (`unavailable` always, `timeout` via the
   per-model `penalize_on_timeout`).
2. An interrupted run leaves a `.out` file in `model-outputs/` with no journal line. Bash runs a
   trap only after the foreground child exits, so with the current foreground `timeout ... bash -c`
   a SIGTERM to model-run.sh would wait up to the model timeout (420 s for glm-4.7).
