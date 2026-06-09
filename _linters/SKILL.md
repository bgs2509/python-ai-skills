---
name: _linters
description: >
  Python linters and static analysis (Ruff, Mypy, Bandit, pre-commit hooks, CI pipeline).
  TRIGGER when: configuring Ruff/Mypy/Bandit, setting up pre-commit hooks,
  building a CI lint/type pipeline, fixing lint or type errors.
  SKIP when: writing tests (use _testing), principle-level code review (use _code-quality),
  security audit beyond Bandit (use _security).
---

# Linters and Static Analysis

> Configuration in `pyproject.toml` (SSoT). Ruff replaces flake8 + isort + black.

## Tools

| Tool | Purpose | Required |
|------|---------|----------|
| Ruff | Linting + formatting | Required |
| Mypy | Static typing | Required |
| Bandit | Security analysis | Recommended |
| Pre-commit | Local hooks | Required |
| Gitleaks | Secret detection | Required |

## Commands

```bash
ruff check .              # Lint
ruff check --fix .        # Autofix
ruff format .             # Format
mypy src/                 # Types
bandit -r src/ -ll        # Security
make ci                   # All checks
```

## CI Pipeline Order

```
lint → format → typecheck → tests → coverage (≥90%) → security
```

Fast checks first — saves time when errors occur.

## Pre-commit Hooks

Security: gitleaks + detect-secrets. Python: ruff + mypy. General: check-yaml, check-json, no-commit-to-branch.

Full configuration: see [reference/linters.md](reference/linters.md)
CI/CD pipeline: see [reference/ci-cd.md](reference/ci-cd.md)
