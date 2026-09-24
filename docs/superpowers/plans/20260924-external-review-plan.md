# Plan: external code review in do-feature Step 12 (bd python-ai-skills-xp4)

Discovery/design: docs/superpowers/specs/20260924-external-review-{discovery,design}.md (DQ-1..3 decided by the user).
Files (one context window): claude-home/scripts/model-run.sh, claude-home/scripts/test_model_run.py, claude-home/model-registry.json, do-feature/reviewer-prompt.md (new), do-feature/SKILL.md, do-feature/reference.md, docs/adr/ADR-003-external-review-step-12.md (new), claude-home/CLAUDE.md, CHANGELOG.md.

1. RED (D-4, D-8): tests — codex dry-run command contains `-o "$MODEL_RUN_ANSWER_FILE"`; a cmd_template writing a log to stdout and the answer to $MODEL_RUN_ANSWER_FILE delivers only the answer to --out; --expect is checked against the answer file; an empty answer file falls back to stdout; a non-ok attempt keeps the log and leaves no answer file; shipped registry has role reviewer = [gpt-sol-xhigh, glm-5.3-high, opus-xhigh], timeout 1800.
2. GREEN: model-run.sh answer file; registry reviewer role (D-1).
3. Template do-feature/reviewer-prompt.md (D-2) with placeholders and the D-3 verdict line; check that the --expect regex does not match the filled template.
4. do-feature SKILL.md (D-6) and reference.md Step 12 procedure (D-5); ADR-003 (D-7); CLAUDE.md role list; CHANGELOG.
5. Verify: make test; pre-commit; dry-run `--role reviewer`.
6. Step 12 of THIS feature uses the new procedure (dogfooding): external review of the xp4 commits, orchestrator verifies findings, fixes.

Self-review: FR-1 -> D-6/D-5 + step 6; FR-2 -> D-2; FR-3 -> D-3 + tests; FR-4 -> registry order + D-5 exception log; FR-5 -> D-5; FR-6 -> D-5 worktree; FR-7 -> D-6/D-7; NFR-1 -> D-4 tests; NFR-2 -> step 5. No placeholders.
