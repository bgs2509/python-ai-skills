---
name: http-clients
description: >
  HTTP-клиенты Python (httpx AsyncClient, timeout, retry, Circuit Breaker,
  централизованное логирование). Используй при интеграции с внешними API.
---

# HTTP-клиенты

> Единый базовый HTTP-клиент (DRY, SSoT). Все исходящие вызовы через него.

## httpx AsyncClient

- Один экземпляр на lifetime приложения
- Connection pooling
- Конкретные клиенты наследуются от базового

## Timeout (обязательно)

| Параметр | Рекомендация |
|----------|-------------|
| connect | 5s |
| read | 30s |
| write | 10s |
| pool | 10s |

Без таймаута — blocker.

## Retry

Retryable: 5xx, Timeout, Connection error, 429 (после Retry-After).
Non-retryable: 4xx.
Стратегия: Exponential backoff + jitter, 3-5 попыток.

## Circuit Breaker

| Состояние | Описание |
|-----------|----------|
| Closed | Нормальная работа |
| Open | Порог ошибок превышен → fallback |
| Half-Open | Пробный запрос |

## Централизованное логирование (автоматическое)

service, operation, method, endpoint, duration_ms, status_code, error_type, is_retryable.

Полная версия: см. [reference.md](reference.md)
