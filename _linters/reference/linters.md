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

## Vulture — Dead Code

Makes the deletion test of `_code-quality/principles.md` mechanical: a commit that leaves an
unused function, class, method, attribute or variable is refused.

Vulture scores unused functions, classes, methods, attributes and variables at 60% confidence
(imports 90%, arguments and unreachable code 100%), so `min_confidence` above 60 never reports
an unused function. Vulture needs the whole codebase to decide what is unused, so the hook takes
its targets from `paths`, not from the staged files.

### Configuration (`pyproject.toml`)

```toml
[tool.vulture]
paths = ["src", "tests", "vulture_whitelist.py"]
min_confidence = 60
# Code a framework calls by itself: route and bot handlers, fixtures, validators.
ignore_decorators = ["@app.*", "@dp.*", "@pytest.fixture", "@pytest_asyncio.fixture", "@field_validator", "@model_validator"]
# pytest and pydantic magic names; BaseHTTPRequestHandler overrides.
ignore_names = ["pytestmark", "model_config", "do_*", "log_message"]

# The whitelist is bare names with long path comments; Ruff fails it otherwise (F821, B018, E501).
[tool.ruff.lint.per-file-ignores]
"vulture_whitelist.py" = ["F821", "B018", "E501"]
```

`tests` is in `paths` on purpose: code a test calls is not excess by the deletion test. Every
entry of `paths` must exist — vulture exits 1 on a missing one; drop `tests` if there is none.

### Enabling it in a project

Run once in every project, new or existing. An existing project fails the first run: model
fields, mock attributes and unused arguments remain after the ignores above (3, 25 and 50
findings in three dev projects, 2026-10-14). The whitelist records them as a reviewed baseline,
so only new dead code blocks a commit; in a new project it stays empty.

```bash
vulture --make-whitelist > vulture_whitelist.py # the shell creates the file first, so paths resolves;
                                                # exits 3 while it lists findings, the file is written
```

Use the vulture version pinned in the hook's `rev`. Read the generated file before committing it:
delete real dead code instead of whitelisting it.

### Commands

```bash
pre-commit run vulture --all-files  # Check with the pinned hook (reads [tool.vulture])
vulture --make-whitelist            # Print current findings as whitelist entries
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

# Vulture — dead code; targets come from [tool.vulture] paths (see "Vulture — Dead Code")
- repo: https://github.com/jendrikseipp/vulture
  rev: v2.16
  hooks:
    - id: vulture
      always_run: true  # a commit that only deletes a caller stages no .py file to trigger it
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

dead-code:      ## Find unused code (pinned pre-commit hook)
	pre-commit run vulture --all-files

ci:             ## Run all checks locally
	ruff check . && ruff format . --check && mypy src/ && pre-commit run vulture --all-files && pytest --cov=src --cov-fail-under=90
```

---

## Summary Table

| Tool | Purpose | Config | Mandatory |
|------|---------|--------|-----------|
| Ruff | Linting + formatting | `[tool.ruff]` | Mandatory |
| Mypy | Static typing | `[tool.mypy]` | Mandatory |
| Bandit | Security analysis | — | Recommended |
| Vulture | Dead code | `[tool.vulture]` | Mandatory |
| Pre-commit | Local hooks | `.pre-commit-config.yaml` | Mandatory |
| Gitleaks | Secret detection | In pre-commit | Mandatory |
| Hadolint | Dockerfile linting | In pre-commit | Recommended |
