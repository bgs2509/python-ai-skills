# Специфика микросервисной архитектуры

> Каждый сервис — изолированный Bounded Context. Коммуникация только через сеть. Внутри каждого сервиса — та же структура (см. skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md)).

---

## Принципы изоляции

| Правило | Описание |
|---------|----------|
| Изоляция кода | Каждый сервис — отдельный репозиторий или директория, свой pyproject.toml |
| Изоляция данных | Каждый сервис владеет своей БД. Shared DB — blocker (SSoT) |
| Изоляция деплоя | Каждый сервис деплоится независимо |
| Изоляция команды | Команда владеет сервисом целиком |

---

## Data API как единственная точка доступа

- Данные доступны ТОЛЬКО через API сервиса-владельца (SSoT)
- Никаких прямых подключений к чужой БД
- Business API → Data API через HTTP (DIP — зависимость от интерфейса)
- Data API предоставляет CRUD + специфичные операции

```
Business API  ──HTTP──►  Data API  ──SQL──►  PostgreSQL
(бизнес-логика)          (доступ к данным)    (данные)
```

---

## Коммуникация между сервисами

### Синхронная (HTTP)

- REST или gRPC
- Timeout обязателен для каждого вызова (Fail Fast)
- Retry только для idempotent операций и retryable ошибок
- Circuit Breaker для защиты от каскадных сбоев

> Детали HTTP-клиентов (timeout, retry, circuit breaker) — см. skill `_http-clients` (_http-clients/reference.md).

### Асинхронная (Events)

- Message broker (RabbitMQ, Kafka, Redis Streams)
- Eventual consistency — данные согласуются не мгновенно
- Idempotent consumers — повторная обработка события безопасна
- Dead Letter Queue для необработанных сообщений

---

## Correlation ID для трейсинга

- Каждый запрос получает уникальный `request_id` на входе (API Gateway)
- `correlation_id` передаётся между сервисами через HTTP-заголовок `X-Correlation-ID`
- Все логи содержат `correlation_id` — восстановление цепочки вызовов (DRY — см. skill `_logging` (_logging/reference.md))
- Единый формат логирования во всех сервисах (SSoT)

---

## Паттерны

### API Gateway

- Единая точка входа для клиентов (SSoT для маршрутизации)
- Маршрутизация, аутентификация, rate limiting
- Nginx или dedicated API Gateway

### Circuit Breaker

> Детали паттерна (состояния, fallback) — см. skill `_http-clients` (_http-clients/reference.md).

### Retry

> Retry-стратегии (retryable/non-retryable, backoff, jitter) — см. skill `_error-handling` (_error-handling/reference.md).

---

## Eventual Consistency

- Данные между сервисами согласуются асинхронно
- Компенсирующие транзакции (Saga) для откатов
- Idempotency key для дедупликации
- Мониторинг задержки согласования

---

## Структура сервиса

Каждый сервис внутри — DDD/Hexagonal (см. skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md)):

```
service-name/
├── src/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── core/                # Конфиг, логирование, исключения (SSoT внутри сервиса)
│   └── main.py
├── tests/
├── Dockerfile
├── pyproject.toml
└── .env.example
```

---

## Риски и антипаттерны

| Риск | Описание | Как избежать |
|------|----------|-------------|
| Distributed monolith | Микросервисы с tight coupling | Изоляция данных, асинхронная коммуникация |
| Shared DB | Несколько сервисов пишут в одну БД | Каждый сервис — своя БД (SSoT) |
| Отсутствие трейсинга | Невозможно отследить запрос | Correlation ID во всех сервисах |
| Каскадный сбой | Сбой одного сервиса роняет все | Circuit Breaker, timeout, fallback |
| Over-splitting | Слишком мелкие сервисы | Один сервис = один Bounded Context |
