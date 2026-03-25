# Linters and Static Analysis

> Unified set of tools for code quality checking. Configuration in `pyproject.toml` (SSoT).

---

## Ruff — Linting + Formatting (SSoT)

A single tool replacing flake8 + isort + black + pyupgrade.

### Configuration (`pyproject.toml`)

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

### Commands

```bash
ruff check .              # Check
ruff check --fix .        # Auto-fix
ruff format .             # Format
ruff format --check .     # Check formatting (CI)
```

---

## Mypy — Static Type Checking

### Configuration (`pyproject.toml`)

```toml
[tool.mypy]
python_version = "3.11"
strict = false
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Commands

```bash
mypy src/                 # Type checking
mypy src/ --strict        # Strict mode
```

---

## Bandit — Security Scanner

- Detects common vulnerabilities in Python code
- 0 high/critical issues = mandatory

```bash
bandit -r src/ -ll        # Check (low + medium + high)
```

---

## Pre-commit Hooks

Automatic checks before every commit. Installation: `pip install pre-commit && pre-commit install`.

### Security: Secret Detection

```yaml
# Gitleaks — fast secret scanner
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.1
  hooks:
    - id: gitleaks
      exclude: \.env\.example$

# Detect-secrets — additional scanner
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ["--baseline", ".secrets.baseline"]
      exclude: |
        (?x)^(
          .*\.env\.example$|
          .*test_.*\.py$|
          \.secrets\.baseline$
        )$
```

### Python: Code Quality

```yaml
# Ruff — linting + formatting
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.9
  hooks:
    - id: ruff
      args: ["--fix", "--exit-non-zero-on-fix"]
    - id: ruff-format

# Mypy — static type checking
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.8.0
  hooks:
    - id: mypy
      additional_dependencies: [pydantic, pydantic-settings, fastapi, structlog]
      args: ["--ignore-missing-imports"]
      files: ^src/.*\.py$
```

### General Checks

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.5.0
  hooks:
    - id: check-added-large-files
      args: ["--maxkb=500"]
    - id: check-yaml
      args: ["--unsafe"]
    - id: check-json
    - id: check-toml
    - id: no-commit-to-branch
      args: ["--branch", "main", "--branch", "master"]
    - id: end-of-file-fixer
    - id: trailing-whitespace
    - id: check-merge-conflict
    - id: check-case-conflict
```

### Blocking Secret Files

```yaml
- repo: local
  hooks:
    - id: check-secrets-files
      name: Block secret files from commit
      entry: bash -c 'echo "ERROR: Attempting to commit secret files!" && exit 1'
      language: system
      files: |
        (?x)^(
          .*\.env$|
          .*\.env\.local$|
          .*\.env\.[^.]+\.local$|
          .*\.pem$|
          .*\.key$|
          .*credentials\.json$|
          .*secrets\.json$
        )$
      pass_filenames: false
```

### Docker: Dockerfile Linting

```yaml
- repo: https://github.com/hadolint/hadolint
  rev: v2.12.0
  hooks:
    - id: hadolint-docker
      args: ["--ignore", "DL3008", "--ignore", "DL3013"]
```

---

## Makefile Commands (DRY)

```makefile
lint:           ## Check code with linter
	ruff check .

lint-fix:       ## Fix linter errors
	ruff check . --fix

format:         ## Format code
	ruff format .

format-check:   ## Check formatting
	ruff format . --check

type-check:     ## Type checking
	mypy src/

ci:             ## Run all checks locally
	ruff check . && ruff format . --check && mypy src/ && pytest --cov=src --cov-fail-under=90
```

---

## Summary Table

| Tool | Purpose | Config | Mandatory |
|------|---------|--------|-----------|
| Ruff | Linting + formatting | `[tool.ruff]` | Mandatory |
| Mypy | Static typing | `[tool.mypy]` | Mandatory |
| Bandit | Security analysis | — | Recommended |
| Pre-commit | Local hooks | `.pre-commit-config.yaml` | Mandatory |
| Gitleaks | Secret detection | In pre-commit | Mandatory |
| Hadolint | Dockerfile linting | In pre-commit | Recommended |
