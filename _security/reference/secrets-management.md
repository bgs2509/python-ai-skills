# Secrets Management

> Environment variables as the single source of secrets (SSoT). No secrets in code, git, or Docker images.

---

## Pydantic Settings (SSoT)

- All settings via `pydantic-settings`
- Typed validation at startup (Fail Fast)
- Required fields without defaults — the application will not start without them
- Single `Settings` class in `core/config.py` (SSoT)

```
class Settings(BaseSettings):
    database_url: str                    # Required — no default
    redis_url: str                       # Required — no default
    secret_key: str                      # Required — no default
    debug: bool = False                  # Optional — has default
    log_level: str = "INFO"              # Optional — has default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

---

## .env.example

- Template without real values — only CHANGE_ME
- Stored in git
- Description for each variable

```
# Database
DATABASE_URL=postgresql+asyncpg://user:CHANGE_ME@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=CHANGE_ME

# Application
DEBUG=false
LOG_LEVEL=INFO
```

---

## Docker

- Pass secrets via `environment:` in docker-compose
- NEVER via build args (they remain in image layers)
- NEVER via COPY .env in Dockerfile

```yaml
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
```

---

## Pre-commit Checks

Automatic blocking of secrets in commits — see skill `_linters` (_linters/reference/linters.md):
- gitleaks — secret scanner
- detect-secrets — additional scanner
- Blocking files: .env, .pem, .key, credentials.json

---

## Secret Rotation

- Zero-downtime procedure: new secret → deploy → revoke old one
- Do not keep old secrets "just in case"
- Log the rotation event (without values) — INFO

---

## Prohibitions (blocker)

| Anti-pattern | Why it is bad |
|--------------|---------------|
| Hardcoded secrets in code | Leak via git |
| Secrets in Docker image | Leak via registry |
| Secrets in logs | Leak via log aggregator |
| `.env` in git | Secret leak |
| Default value for a secret | Application starts with an invalid secret |
| Secrets in CI/CD configs | Leak via CI/CD system |
