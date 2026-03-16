# CI/CD

> Автоматический pipeline проверок. Быстрые проверки первыми. Детали инструментов — см. skill `linters` (linters/reference/linters.md) (DRY).

---

## Обязательный pipeline

```
lint (ruff check) → format (ruff format --check) → typecheck (mypy) → tests (pytest --cov) → coverage (≥90%) → security (bandit)
```

**Порядок обязателен**: быстрые проверки первыми — экономия времени при ошибках.

| Шаг | Инструмент | Порог | Время |
|-----|-----------|-------|-------|
| Lint | ruff check | 0 ошибок | ~2s |
| Format | ruff format --check | Соответствует | ~2s |
| Typecheck | mypy | 0 errors | ~10s |
| Tests | pytest | Все проходят | ~30s+ |
| Coverage | pytest --cov | ≥90% | (вместе с тестами) |
| Security | bandit | 0 high/critical | ~5s |

---

## Coverage gate

- Порог: ≥90%
- Pipeline fails если покрытие ниже порога
- Команда: `pytest --cov=src --cov-report=xml --cov-fail-under=90`
- Отчёт: XML для CI, HTML для локальной разработки

---

## Docker build в CI

- Multi-stage build (см. skill `docker` (docker/reference/docker.md))
- Кэширование слоёв — зависимости отдельно от кода
- Build + healthcheck как финальный шаг pipeline

```bash
docker build -t app:ci .
docker run --rm app:ci python -c "import src; print('OK')"
```

---

## Локальный CI

Перед push — запусти все проверки локально:

```bash
make ci
```

> Команда `make ci` и конфигурация инструментов — см. skill `linters` (linters/reference/linters.md).

> Детали тестирования (уровни, фикстуры, покрытие) — см. skill `testing` (testing/reference.md).
