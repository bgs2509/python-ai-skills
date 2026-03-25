---
name: _report
description: >
  Create a completion report for a feature, refactoring, or critical bug fix.
  Template with review and test results. Invoke after completing significant work.
  TRIGGER when: feature is implemented and ready to commit, refactoring is complete,
  critical bug is fixed, user says "done/ready/commit".
---

# Completion Report

> Report after completing a feature. Records what was done, what was verified, what doesn't work.

## When to Create

- After completing a significant feature
- After refactoring
- After fixing a critical bug
- Before merging into main

## Actions

1. Ask the user for the Task ID (if not obvious)
2. Gather data: changed files, tests, coverage
3. Create a file using the template below
4. Save to `docs/reports/{date}-{feature}.md`

## Template

```markdown
# Completion Report: {Title}

## Task
- Task ID: {TASK-NNN}
- Plan: {PLAN-NNN or "None"}
- ADR: {ADR-NNN or "None"}

## Executive Summary
{1-3 sentences: what was done and why}

## Changes
### Added / Changed / Removed

## Review Results
- [ ] Quality Cascade — verified
- [ ] Security checklist — verified
- [ ] Linters passed

## Test Results
- Unit: {passed}/{total}
- Integration: {passed}/{total}
- Coverage: {N}%

## Known Limitations
{What doesn't work, workarounds, or "None"}

## Metrics
- Files changed / Lines added / removed / Tests added
```

## Rules

| Rule | Description |
|------|-------------|
| Language | Russian |

Full version: see [reference.md](reference.md)
