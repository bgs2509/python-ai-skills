# Линтеры и статический анализ

> Единый набор инструментов для проверки качества кода. Конфигурация — в `pyproject.toml` (SSoT).

---

## Ruff — линтинг + форматирование (SSoT)

Единый инструмент вместо flake8 + isort + black + pyupgrade.

### Конфигурация (`pyproject.toml`)

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

### Команды

```bash
ruff check .              # Проверка
ruff check --fix .        # Автоисправление
ruff format .             # Форматирование
ruff format --check .     # Проверка форматирования (CI)
```

---

## Mypy — статическая проверка типов

### Конфигурация (`pyproject.toml`)

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

### Команды

```bash
mypy src/                 # Проверка типов
mypy src/ --strict        # Строгий режим
```

---

## Bandit — security-сканер

- Находит распространённые уязвимости в Python-коде
- 0 high/critical issues = обязательно

```bash
bandit -r src/ -ll        # Проверка (low + medium + high)
```

---

## Pre-commit hooks

Автоматические проверки перед каждым коммитом. Установка: `pip install pre-commit && pre-commit install`.

### Security: обнаружение секретов

```yaml
# Gitleaks — быстрый сканер секретов
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.1
  hooks:
    - id: gitleaks
      exclude: \.env\.example$

# Detect-secrets — дополнительный сканер
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

### Python: качество кода

```yaml
# Ruff — линтинг + форматирование
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.9
  hooks:
    - id: ruff
      args: ["--fix", "--exit-non-zero-on-fix"]
    - id: ruff-format

# Mypy — статическая проверка типов
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.8.0
  hooks:
    - id: mypy
      additional_dependencies: [pydantic, pydantic-settings, fastapi, structlog]
      args: ["--ignore-missing-imports"]
      files: ^src/.*\.py$
```

### Общие проверки

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

### Блокировка секретных файлов

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

### Docker: lint Dockerfile

```yaml
- repo: https://github.com/hadolint/hadolint
  rev: v2.12.0
  hooks:
    - id: hadolint-docker
      args: ["--ignore", "DL3008", "--ignore", "DL3013"]
```

---

## Makefile команды (DRY)

```makefile
lint:           ## Проверить код линтером
	ruff check .

lint-fix:       ## Исправить ошибки линтера
	ruff check . --fix

format:         ## Отформатировать код
	ruff format .

format-check:   ## Проверить форматирование
	ruff format . --check

type-check:     ## Проверка типов
	mypy src/

ci:             ## Запустить все проверки локально
	ruff check . && ruff format . --check && mypy src/ && pytest --cov=src --cov-fail-under=90
```

---

## Итоговая таблица

| Инструмент | Назначение | Конфиг | Обязательность |
|------------|-----------|--------|----------------|
| Ruff | Линтинг + форматирование | `[tool.ruff]` | Обязательно |
| Mypy | Статическая типизация | `[tool.mypy]` | Обязательно |
| Bandit | Security-анализ | — | Рекомендуется |
| Pre-commit | Локальные хуки | `.pre-commit-config.yaml` | Обязательно |
| Gitleaks | Обнаружение секретов | В pre-commit | Обязательно |
| Hadolint | Lint Dockerfile | В pre-commit | Рекомендуется |
