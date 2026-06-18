# audit-loop smoke-test fixture

Minimal dev-workflow project to validate the skill end-to-end.

## Layout

```
test/fixture/
├── .pre-commit-config.yaml
├── pyproject.toml
├── docs/
│   ├── superpowers/.keep        # dev-workflow detection marker
│   ├── development-plan.xml
│   ├── knowledge-graph.xml
│   └── verification-plan.xml
├── src/
│   └── buggy_module.py          # 3 planted bugs
└── tests/
    └── test_buggy.py
```

## Planted bugs (expected codex findings)

1. **`fetch_user` — missing `await`** on `client.get(...)` (critical, category=bug, kind=missing-await)
2. **`dedupe_emails` — DRY violation** — two near-identical normalization passes (medium, category=principle, kind=dry-violation)
3. **`classify_priority` — dead branch** — `score > 100` unreachable after `score > 50` returns (medium, category=bug, kind=dead-branch)

## Smoke test (dry-run, safe — no commits, no fixes)

```bash
cd ~/.claude/skills/audit-loop/test/fixture
git init -q && git add -A && git commit -q -m "fixture baseline"
/audit-loop --dry-run --max-rounds=1
```

**Expected output:**
- pre-flight passes (docs/superpowers exists, development-plan.xml exists, pre-commit config exists)
- codex finds ≥3 findings (the planted bugs above)
- exit message: `DRY-RUN complete · ≥1c/≥1m/0min · no changes made`
- `docs/audit-loop/dry-run/round-1.json` contains findings with fingerprints
- no commits, no `state.json`, no lock leftover

## Full e2e test (real fixes — destructive, run on disposable copy only)

```bash
cp -r ~/.claude/skills/audit-loop/test/fixture /tmp/audit-fixture-test
cd /tmp/audit-fixture-test
git init -q && git add -A && git commit -q -m "fixture baseline"
/audit-loop --max-rounds=2
# Expected: R1 finds the planted bugs, R2 confirms fixes, no stagnation, final report at docs/reports/.
```
