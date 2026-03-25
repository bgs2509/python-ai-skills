# Caching

> Redis as the primary cache store. Graceful degradation — if the cache is unavailable, the application works without it.

---

## Redis — Connection Pooling

- Single connection pool (SSoT)
- Configuration: max_connections, timeout
- Closed on graceful shutdown
- Health check: ping on startup

---

## Caching Patterns

### Cache-Aside (Lazy Loading)

1. Request → check cache
2. Cache hit → return data
3. Cache miss → query from DB → write to cache → return

Use when: data is read frequently, written rarely.

### Write-Through

1. Write → update DB + update cache simultaneously
2. Read → always from cache

Use when: data must be up-to-date in the cache immediately after writing.

---

## TTL

- Explicit TTL for every key (Explicit > Implicit)
- No infinite caching — always set a TTL
- Different TTLs for different data types:
  - Reference data: 1 hour — 24 hours
  - User data: 5 minutes — 1 hour
  - Sessions: session lifetime
  - Rate limit counters: limit window

---

## Invalidation

| Strategy | When |
|----------|------|
| By TTL | Data expires over time |
| By event | Data changed (write → invalidate cache) |
| Key versioning | Mass invalidation (increment version) |

---

## Key Naming (CoC)

Format: `{service}:{entity}:{id}:{version}`

Examples:
- `users:user:123` — user 123
- `orders:user_orders:456` — orders for user 456
- `config:feature_flags:v2` — feature flags version 2

---

## Serialization

- JSON as the format (SSoT — single format)
- Pydantic models → JSON → Redis
- Redis → JSON → Pydantic models

---

## Graceful Degradation

- If Redis is unavailable — the application works without cache
- Cache miss = query to DB (slower, but works)
- Logging: WARNING when cache is unavailable
- Do not crash due to cache issues

---

## Logging (DRY)

Automatic logging in the base cache client:

| Field | Description |
|-------|-------------|
| operation | get/set/delete/invalidate |
| key | Key (without sensitive data) |
| hit | true/false (for get) |
| ttl | Time-to-live (for set) |
| duration_ms | Operation duration |

> Logging format — see skill `_logging` (_logging/reference.md).

---

## Anti-patterns

| Anti-pattern | Why it is bad |
|--------------|---------------|
| Cache without TTL | Data becomes stale forever |
| Caching secrets | Leak through Redis |
| Cache without graceful degradation | Redis crash = application crash |
| Schedule-based invalidation instead of event-based | Data inconsistency |
| Magic keys without a naming convention | Impossible to find and debug |
