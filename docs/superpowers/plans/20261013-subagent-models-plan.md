# Plan: subagent model routing (bd python-ai-skills-8of.4)

Discovery/design: docs/superpowers/specs/20261013-subagent-models-{discovery,design}.md
Files (one context window): claude-home/hooks/delegation-pool-nudge.sh, claude-home/hooks/test_delegation_pool_nudge.py,
claude-home/model-registry.json, claude-home/scripts/test_model_run.py (shipped-registry checks),
claude-home/scripts/test_skill_stats.py (template check), claude-home/settings.json.template,
do-feature/SKILL.md, CHANGELOG.md, docs/research/skills-revision-plan-2026-10.md.

1. RED: D-6 tests; run the hook and scripts suites; expect the new tests to fail.
2. GREEN: D-3 hook, D-2 + D-4 registry, D-1 template.
3. Docs: D-5; CHANGELOG; plan doc 3a/3b/3c marked done.
4. Verify: `make test`; live check — a `claude -p` session launching a subagent without `model` shows the hint.
5. Review via `model-run.sh --role reviewer`; render settings (`make install-symlinks`); close bd.

Self-review: FR-1 -> template test; FR-2 -> registry test; FR-3 -> hook tests; FR-4 -> combined test + unchanged suite; FR-5 -> registry test + doc edit; NFR-1 -> broken-registry and malformed tests; NFR-2 -> synthetic-registry test proves names come from the registry; NFR-3 -> make test. No placeholders.
