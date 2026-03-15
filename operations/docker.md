# Docker

> Контейнеризация приложения. Минимальный размер, безопасность, кэширование слоёв.

---

## Dockerfile — Multi-stage build

### Принципы

| Правило | Описание |
|---------|----------|
| Multi-stage build | Builder (зависимости) → Runtime (минимальный образ) |
| Non-root user | Приложение работает от непривилегированного пользователя |
| Порядок слоёв | Зависимости → Код (кэширование: зависимости меняются реже) |
| Минимальный размер | python:3.11-slim, не python:3.11 |
| Без dev-зависимостей | В production только runtime зависимости |

### Порядок слоёв (кэширование)

```dockerfile
# 1. Базовый образ (меняется редко)
FROM python:3.11-slim as builder

# 2. Системные зависимости (меняются редко)
RUN apt-get update && apt-get install -y --no-install-recommends ...

# 3. Python зависимости (меняются иногда)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Код приложения (меняется часто)
COPY src/ ./src/

# Runtime stage
FROM python:3.11-slim
# ...копируем только нужное из builder
```

---

## Docker Compose

- Сервисы, сети, volumes
- Healthcheck для каждого сервиса
- Depends_on с condition: service_healthy
- Секреты через environment — см. `operations/secrets-management.md`

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## Security

| Правило | Как |
|---------|-----|
| Non-root user | `RUN adduser --disabled-password appuser` + `USER appuser` |
| No new privileges | `security_opt: - no-new-privileges:true` |
| Drop capabilities | `cap_drop: - ALL` |
| Read-only filesystem | `read_only: true` + tmpfs для /tmp |
| Без секретов в image | Не COPY .env, не ARG для секретов |

---

## .dockerignore

```
.git
.env
.env.*
*.pem
*.key
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
htmlcov
.coverage
tests/
docs/
*.md
.claude/
```

---

## Полезные команды

```bash
# Сборка
docker compose build

# Запуск
docker compose up -d

# Логи
docker compose logs -f app

# Остановка
docker compose down

# Пересборка без кэша
docker compose build --no-cache
```
