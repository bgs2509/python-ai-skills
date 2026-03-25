# Docker

> Application containerization. Minimal size, security, layer caching.

---

## Dockerfile — Multi-stage Build

### Principles

| Rule | Description |
|------|-------------|
| Multi-stage build | Builder (dependencies) → Runtime (minimal image) |
| Non-root user | Application runs as a non-privileged user |
| Layer order | Dependencies → Code (caching: dependencies change less frequently) |
| Minimal size | python:3.11-slim, not python:3.11 |
| No dev dependencies | Only runtime dependencies in production |

### Layer Order (caching)

```dockerfile
# 1. Base image (changes rarely)
FROM python:3.11-slim as builder

# 2. System dependencies (change rarely)
RUN apt-get update && apt-get install -y --no-install-recommends ...

# 3. Python dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Application code (changes frequently)
COPY src/ ./src/

# Runtime stage
FROM python:3.11-slim
# ...copy only what is needed from builder
```

---

## Docker Compose

- Services, networks, volumes
- Healthcheck for each service
- Depends_on with condition: service_healthy
- Secrets via environment — see skill `_security` (_security/reference/secrets-management.md)

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

| Rule | How |
|------|-----|
| Non-root user | `RUN adduser --disabled-password appuser` + `USER appuser` |
| No secrets in image | Do not COPY .env, do not use ARG for secrets |

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

## Useful Commands

```bash
# Build
docker compose build

# Start
docker compose up -d

# Logs
docker compose logs -f app

# Stop
docker compose down

# Rebuild without cache
docker compose build --no-cache
```
