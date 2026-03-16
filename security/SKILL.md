---
name: security
description: >
  Безопасность Python-приложений: OWASP Top 10 чеклист, валидация, CORS, rate limiting,
  управление секретами (Pydantic Settings, .env.example). Используй при ревью безопасности, настройке секретов, аудите.
---

# Security

> Безопасность на всех уровнях — от ввода до логов. Секреты через environment variables (SSoT).

## Обязательные правила

| Правило | Детали |
|---------|--------|
| Секреты только через env vars | Никаких hardcoded паролей, токенов, API-ключей |
| .gitignore | .env, *.pem, *.key, credentials.json |
| .env.example без секретов | Только CHANGE_ME placeholder'ы |
| Санитизация логов | Автоматическая маскировка через structlog |
| Валидация на границах | Pydantic, Fail Fast |
| Параметризованные SQL | SQL injection — blocker |
| CORS (не `*` в prod) | Явный список origins |
| Rate limiting | Для публичных endpoints |
| HTTPS only в prod | Незашифрованный трафик недопустим |
| Pre-commit hooks | Автоматическая проверка утечки секретов |

## OWASP Top 10

| # | Уязвимость | Предотвращение |
|---|-----------|----------------|
| 1 | Injection | Параметризованные запросы, ORM |
| 2 | Broken Auth | bcrypt/argon2, сессии с таймаутом |
| 3 | Sensitive Data | HTTPS, маскировка в логах |
| 4 | XXE | Отключение внешних сущностей |
| 5 | Broken Access | Проверка прав, deny by default |
| 6 | Misconfiguration | Нет дефолтных паролей, debug=False |
| 7 | XSS | Экранирование, CSP |
| 8 | Insecure Deserialization | Pydantic для валидации |
| 9 | Known Vulnerabilities | Обновление зависимостей |
| 10 | Insufficient Logging | Логирование security-событий |

Управление секретами (Pydantic Settings, ротация): см. [reference/secrets-management.md](reference/secrets-management.md)
Полная версия security-правил: см. [reference/security.md](reference/security.md)
