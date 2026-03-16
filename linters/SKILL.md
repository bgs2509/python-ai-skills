---
name: linters
description: >
  Линтеры и статический анализ Python (Ruff, Mypy, Bandit, pre-commit hooks, CI pipeline).
  Используй при настройке линтеров, CI/CD, pre-commit, проверке качества кода.
---

# Линтеры и статический анализ

> Конфигурация — в `pyproject.toml` (SSoT). Ruff заменяет flake8 + isort + black.

## Инструменты

| Инструмент | Назначение | Обязательность |
|------------|-----------|----------------|
| Ruff | Линтинг + форматирование | Обязательно |
| Mypy | Статическая типизация | Обязательно |
| Bandit | Security-анализ | Рекомендуется |
| Pre-commit | Локальные хуки | Обязательно |
| Gitleaks | Обнаружение секретов | Обязательно |

## Команды

```bash
ruff check .              # Lint
ruff check --fix .        # Autofix
ruff format .             # Format
mypy src/                 # Types
bandit -r src/ -ll        # Security
make ci                   # All checks
```

## CI Pipeline порядок

```
lint → format → typecheck → tests → coverage (≥90%) → security
```

Быстрые проверки первыми — экономия времени при ошибках.

## Pre-commit hooks

Security: gitleaks + detect-secrets. Python: ruff + mypy. Общие: check-yaml, check-json, no-commit-to-branch.

Полная конфигурация: см. [reference/linters.md](reference/linters.md)
CI/CD pipeline: см. [reference/ci-cd.md](reference/ci-cd.md)
