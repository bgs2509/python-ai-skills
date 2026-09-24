# Plan: model-run policy and interrupt handling (bd python-ai-skills-xwa)

Discovery: docs/superpowers/specs/20260924-model-run-policy-trap-discovery.md
Design: docs/superpowers/specs/20260924-model-run-policy-trap-design.md
Files (one context window): claude-home/scripts/model-run.sh, claude-home/scripts/test_model_run.py,
claude-home/model-registry.json, CHANGELOG.md.

1. RED: add design tests 1-5 to test_model_run.py; run `python3 -m pytest claude-home/scripts/test_model_run.py -q`; expect 1, 3, 4, 5 to fail (2 passes today).
2. GREEN D-1: read `policy.penalize_on` in model-run.sh; replace the hardcoded `unavailable`/`timeout` penalty branches with one membership check plus the `penalize_on_timeout` override; drop `no_penalty_on` from the registry and update its policy comment.
3. GREEN D-2: background+wait attempt, INT/TERM trap journalling `interrupted`; header documents the outcome and exit codes.
4. Verify: `make test`; `pre-commit run --files <changed>`; commit `fix(model-run): ...` and `feat(model-registry)`-free (registry change rides with the code that reads it).
5. CHANGELOG Fixed entry; close bd.

Self-review: FR-1 -> tests 1,2; FR-2 -> test 3; FR-3 -> test 4; FR-4 -> test 5; NFR-1 by construction; NFR-2 step 4. No placeholders.
