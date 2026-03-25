# CI/CD

> Automated checks pipeline. Fast checks first. Tool details — see skill `_linters` (_linters/reference/linters.md) (DRY).

---

## Mandatory Pipeline

```
lint (ruff check) → format (ruff format --check) → typecheck (mypy) → tests (pytest --cov) → coverage (≥90%) → security (bandit)
```

**Order is mandatory**: fast checks first — saving time on failures.

| Step | Tool | Threshold | Time |
|------|------|-----------|------|
| Lint | ruff check | 0 errors | ~2s |
| Format | ruff format --check | Compliant | ~2s |
| Typecheck | mypy | 0 errors | ~10s |
| Tests | pytest | All pass | ~30s+ |
| Coverage | pytest --cov | ≥90% | (together with tests) |
| Security | bandit | 0 high/critical | ~5s |

---

## Coverage Gate

- Threshold: ≥90%
- Pipeline fails if coverage is below the threshold
- Command: `pytest --cov=src --cov-report=xml --cov-fail-under=90`
- Report: XML for CI, HTML for local development

---

## Docker Build in CI

- Multi-stage build (see skill `_docker` (_docker/reference/docker.md))
- Layer caching — dependencies separate from code
- Build + healthcheck as the final pipeline step

```bash
docker build -t app:ci .
docker run --rm app:ci python -c "import src; print('OK')"
```

---

## Local CI

Before push — run all checks locally:

```bash
make ci
```

> The `make ci` command and tool configuration — see skill `_linters` (_linters/reference/linters.md).

> Testing details (levels, fixtures, coverage) — see skill `_testing` (_testing/reference.md).
