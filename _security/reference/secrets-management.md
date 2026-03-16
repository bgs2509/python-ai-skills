# Управление секретами

> Environment variables как единственный источник секретов (SSoT). Никаких секретов в коде, git, Docker images.

---

## Pydantic Settings (SSoT)

- Все настройки — через `pydantic-settings`
- Типизированная валидация при старте (Fail Fast)
- Обязательные поля без default — приложение не запустится без них
- Единый класс `Settings` в `core/config.py` (SSoT)

```
class Settings(BaseSettings):
    database_url: str                    # Обязательно — нет default
    redis_url: str                       # Обязательно — нет default
    secret_key: str                      # Обязательно — нет default
    debug: bool = False                  # Опционально — есть default
    log_level: str = "INFO"              # Опционально — есть default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

---

## .env.example

- Шаблон без реальных значений — только CHANGE_ME
- Хранится в git
- Описание каждой переменной

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

- Передача секретов через `environment:` в docker-compose
- НИКОГДА через build args (остаются в image layers)
- НИКОГДА через COPY .env в Dockerfile

```yaml
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
```

---

## Pre-commit проверки

Автоматическая блокировка секретов в коммитах — см. skill `_linters` (_linters/reference/linters.md):
- gitleaks — сканер секретов
- detect-secrets — дополнительный сканер
- Блокировка файлов: .env, .pem, .key, credentials.json

---

## Ротация секретов

- Процедура без downtime: новый секрет → деплой → отзыв старого
- Не хранить старые секреты "на всякий случай"
- Логирование факта ротации (без значений) — INFO

---

## Запреты (blocker)

| Антипаттерн | Почему плохо |
|-------------|-------------|
| Hardcoded секреты в коде | Утечка через git |
| Секреты в Docker image | Утечка через registry |
| Секреты в логах | Утечка через log aggregator |
| `.env` в git | Утечка секретов |
| Default значение для секрета | Приложение запустится с невалидным секретом |
| Секреты в CI/CD конфигах | Утечка через CI/CD систему |
