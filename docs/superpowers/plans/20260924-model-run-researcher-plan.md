# Plan: web-research role (bd python-ai-skills-a67)

Discovery/design: docs/superpowers/specs/20260924-model-run-researcher-{discovery,design}.md
Files (one context window): claude-home/scripts/model-run.sh, claude-home/scripts/test_model_run.py, claude-home/model-registry.json, claude-home/CLAUDE.md, CHANGELOG.md.

1. RED: add the D-3 tests; run `python3 -m pytest claude-home/scripts/test_model_run.py -q`; expect the override, invalid-timeout and shipped-registry tests to fail.
2. GREEN: D-2 in model-run.sh; D-1 in the registry.
3. Docs: D-4; CHANGELOG Added entry.
4. Verify: `make test`; `model-run.sh --role researcher --task <file> --dry-run` shows timeout=900 for all three models; commit.
5. Review (strong tier), fix, close bd.

Self-review: FR-1 -> registry + shipped test; FR-2 -> override tests; FR-3 -> shipped test + dry-run; FR-4 -> shipped test; FR-5 -> docs step + help grep; NFR-1 -> existing suite; NFR-2 -> make test. No placeholders.
