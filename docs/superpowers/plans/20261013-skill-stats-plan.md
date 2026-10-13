# Plan: skill-stats (bd python-ai-skills-8of.1)

Discovery/design: docs/superpowers/specs/20261013-skill-stats-{discovery,design}.md
Files (one context window): claude-home/scripts/skill-stats.py, claude-home/scripts/test_skill_stats.py,
claude-home/settings.json.template, Makefile, CHANGELOG.md, docs/research/skills-revision-plan-2026-10.md.

1. RED: write D-8 tests; run `python3 -m pytest claude-home/scripts/test_skill_stats.py -q`; expect failures (module missing, template 30).
2. GREEN: implement D-1..D-6; set D-7.
3. Wire: add the test file to `make test`; CHANGELOG Added/Changed entries; plan doc step 0 marked done with the tool's name.
4. Verify: `make test`; run the tool on real transcripts, compare with prototype numbers (do-feature calls 34, progress-watch 145, totals within 1 %); commit.
5. Review via `model-run.sh --role reviewer`, fix findings, re-render settings (`make install-symlinks`), close bd.

Self-review: FR-1..FR-3 -> D-2/D-3 tests; FR-4 -> per-skill tests; FR-5 -> cost/first-request tests; FR-6 -> CLI/since/invalid-line tests; FR-7 -> template test; NFR-1 -> stdlib imports only; NFR-2 -> make test + hook regex already covers claude-home/scripts/. No placeholders.
