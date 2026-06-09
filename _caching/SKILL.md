---
name: _caching
description: >
  Python caching (Redis, Cache-Aside, Write-Through, TTL, invalidation,
  graceful degradation).
  TRIGGER when: adding a cache layer, working with Redis, designing TTL/invalidation,
  cache-aside/write-through patterns, graceful degradation on cache miss or outage.
  SKIP when: source-of-truth persistent storage (use _database), client-side HTTP response caching
  (use _http), trivial in-process memoization without Redis.
---

# Caching

> Redis as the primary store. Graceful degradation — the application works without cache.

## Patterns

- **Cache-Aside**: check cache → miss → DB → write to cache. For: frequently read, rarely written.
- **Write-Through**: write → DB + cache simultaneously. For: data must be up-to-date immediately.

## TTL (required)

| Data Type | TTL |
|-----------|-----|
| Reference data | 1-24 hours |
| User data | 5 min — 1 hour |
| Sessions | Session lifetime |
| Rate limit | Limit window |

No TTL — blocker.

## Invalidation

By TTL | By event (write → invalidate) | Key versioning (bulk)

## Key Naming

`{service}:{entity}:{id}` — e.g. `users:user:123`

## Rules

- Single connection pool (SSoT)
- JSON serialization via Pydantic
- Graceful degradation: Redis down → application works without cache (WARNING in logs)
- Do not cache secrets

Full version: see [reference.md](reference.md)
