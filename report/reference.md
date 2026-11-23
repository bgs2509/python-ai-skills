# Completion Report

> Report after finishing a feature. Records what was done, what was verified, what changed, what does not work.

---

## When to Create

- After completing every significant feature
- After refactoring
- After fixing a critical bug
- Before merging to main

---

## Template

```markdown
# Completion Report: {Feature Name}

## Task

- Task ID: {TASK-NNN}
- Plan: {PLAN-NNN or "None"}
- ADR: {ADR-NNN or "None"}

## Executive Summary

{1-3 sentences: what was done and why}

## Changes

### Added
- {What was added}

### Changed
- {What was changed}

### Removed
- {What was removed}

## Review Results

- [ ] Quality Cascade (17 principles) — verified
- [ ] Security checklist — verified
- [ ] Linters passed (ruff, mypy)

## Test Results

- Unit: {passed}/{total}
- Integration: {passed}/{total}
- Coverage: {N}%

## Architecture Decision Records

{List of ADRs created as part of the feature, or "None"}

## Scope Changes

{What differs from the original plan and why, or "None"}

## Known Limitations

{What does not work, workarounds, plans for fixing, or "None"}

## Metrics

- Files changed: {N}
- Lines added: {N}
- Lines deleted: {N}
- Tests added: {N}
```

---

## Rules

| Rule | Description |
|------|-------------|
| Storage | `docs/reports/` in the project repository |
| Naming | `{date}-{feature}.md` (e.g., `2024-01-15-user-auth.md`) |
| Brevity | Executive Summary — 1-3 sentences, not a retelling of all the work |
| Known Limitations | Mandatory section — even if "None" |
| Scope Changes | Mandatory section — recording deviations from the plan |
