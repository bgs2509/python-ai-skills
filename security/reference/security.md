# Security

> Безопасность на всех уровнях — от ввода до логов. Секреты через environment variables (SSoT). Подробнее об управлении секретами — см. skill `security` (security/reference/secrets-management.md).

---

## Обязательные правила

| Правило | Детали |
|---------|--------|
| Секреты только через environment variables | Никаких hardcoded паролей, токенов, API-ключей в коде или git. SSoT — см. skill `security` (security/reference/secrets-management.md). |
| .gitignore содержит .env, *.pem, *.key, credentials.json | Проверяется автоматически. Нарушение = blocker. |
| .env.example без реальных секретов | Только placeholder'ы (CHANGE_ME). |
| Санитизация чувствительных данных в логах | Автоматическая маскировка через structlog процессор (SSoT). См. skill `logging` (logging/reference.md). |
| Валидация на границах системы | Input validation через Pydantic. Не доверяй входным данным (Fail Fast). |
| Параметризованные запросы к БД | SQL injection — blocker. См. skill `database` (database/reference.md). |
| CORS настроен (не `*` в production) | Явный список разрешённых origins. |
| Rate limiting для публичных endpoints | Защита от abuse. |
| HTTPS only в production | Незашифрованный трафик недопустим. |
| Принцип минимальных привилегий | Каждый компонент имеет только необходимые права. |
| Pre-commit hooks | Автоматическая проверка на утечку секретов. См. skill `linters` (linters/reference/linters.md). |
| Fail-fast валидация конфигурации при старте | Обязательные поля без default, валидация формата при инициализации Settings. |

---

## OWASP Top 10 — обязательный чеклист

При каждом ревью проверять отсутствие:

| # | Уязвимость | Как предотвратить |
|---|-----------|-------------------|
| 1 | Injection (SQL, OS, LDAP) | Параметризованные запросы, ORM |
| 2 | Broken Authentication | Безопасное хранение паролей (bcrypt/argon2), сессии с таймаутом |
| 3 | Sensitive Data Exposure | Шифрование в transit (HTTPS) и at rest, маскировка в логах |
| 4 | XML External Entities (XXE) | Отключение внешних сущностей в XML-парсерах |
| 5 | Broken Access Control | Проверка прав на каждом endpoint, deny by default |
| 6 | Security Misconfiguration | Нет дефолтных паролей, debug=False в production |
| 7 | Cross-Site Scripting (XSS) | Экранирование вывода, Content-Security-Policy |
| 8 | Insecure Deserialization | Не десериализовать непроверенные данные, Pydantic для валидации |
| 9 | Using Components with Known Vulnerabilities | Регулярное обновление зависимостей, safety check |
| 10 | Insufficient Logging | Централизованное логирование всех security-событий. См. skill `logging` (logging/reference.md). |

---

## Docker Security

> См. skill `docker` (docker/reference/docker.md) секция "Security".
