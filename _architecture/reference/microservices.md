# Microservices Architecture Specifics

> Each service is an isolated Bounded Context. Communication only over the network. Inside each service — the same structure (see skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md)).

---

## Isolation Principles

| Rule | Description |
|------|-------------|
| Code isolation | Each service is a separate repository or directory, with its own pyproject.toml |
| Data isolation | Each service owns its own DB. Shared DB — blocker (SSoT) |
| Deployment isolation | Each service is deployed independently |
| Team isolation | A team owns the entire service |

---

## Data API as the Single Point of Access

- Data is accessible ONLY through the owning service's API (SSoT)
- No direct connections to another service's DB
- Business API → Data API via HTTP (DIP — dependency on interface)
- Data API provides CRUD + domain-specific operations

```
Business API  ──HTTP──►  Data API  ──SQL──►  PostgreSQL
(business logic)         (data access)       (data)
```

---

## Inter-Service Communication

### Synchronous (HTTP)

- REST or gRPC
- Timeout is mandatory for every call (Fail Fast)
- Retry only for idempotent operations and retryable errors
- Circuit Breaker to protect against cascading failures

> HTTP client details (timeout, retry, circuit breaker) — see skill `_http` (_http/reference.md).

### Asynchronous (Events)

- Message broker (RabbitMQ, Kafka, Redis Streams)
- Eventual consistency — data is not synchronized instantly
- Idempotent consumers — reprocessing an event is safe
- Dead Letter Queue for unprocessed messages

---

## Correlation ID for Tracing

- Each request receives a unique `request_id` at the entry point (API Gateway)
- `correlation_id` is passed between services via the `X-Correlation-ID` HTTP header
- All logs contain `correlation_id` — reconstructing the call chain (DRY — see skill `_logging` (_logging/reference.md))
- Unified logging format across all services (SSoT)

---

## Patterns

### API Gateway

- Single entry point for clients (SSoT for routing)
- Routing, authentication, rate limiting
- Nginx or dedicated API Gateway

### Circuit Breaker

> Pattern details (states, fallback) — see skill `_http` (_http/reference.md).

### Retry

> Retry strategies (retryable/non-retryable, backoff, jitter) — see skill `_error-handling` (_error-handling/reference.md).

---

## Eventual Consistency

- Data between services is synchronized asynchronously
- Compensating transactions (Saga) for rollbacks
- Idempotency key for deduplication
- Monitoring synchronization delay

---

## Service Structure

Each service internally follows DDD/Hexagonal (see skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md)):

```
service-name/
├── src/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── core/                # Config, logging, exceptions (SSoT within the service)
│   └── main.py
├── tests/
├── Dockerfile
├── pyproject.toml
└── .env.example
```

---

## Risks and Anti-patterns

| Risk | Description | How to avoid |
|------|-------------|-------------|
| Distributed monolith | Microservices with tight coupling | Data isolation, asynchronous communication |
| Shared DB | Multiple services write to a single DB | Each service has its own DB (SSoT) |
| Missing tracing | Unable to trace a request | Correlation ID across all services |
| Cascading failure | One service failure brings down all others | Circuit Breaker, timeout, fallback |
| Over-splitting | Services that are too granular | One service = one Bounded Context |
