---
name: _database
description: >
  Database operations in Python (Repository pattern, Alembic migrations, transactions, N+1 problem,
  connection pooling, ORM vs Domain Entities).
  TRIGGER when: writing repositories/queries, Alembic migrations, transaction boundaries,
  fixing N+1, configuring connection pooling, mapping ORM vs domain entities.
  SKIP when: caching layer (use _caching), external non-DB APIs (use _http),
  pure business logic with no persistence.
---

# Database Operations

> Repository is the single access point to data (SSoT, DIP). Business logic NEVER accesses the DB directly.

## Repository Pattern

- Interface in Domain (ABC/Protocol), implementation in Infrastructure (DIP)
- One Repository per entity (SRP)
- Returns domain entities, not ORM models
- Base Repository: get_by_id, get_all, create, update, delete (DRY)

## Migrations (Alembic)

- The sole migration tool (SSoT)
- Each migration is atomic and reversible
- Manual DB changes in production are prohibited

## Key Rules

- **SQL injection — blocker**: parameterized queries only
- **Transactions**: boundaries in Application Service, not in Repository
- **N+1**: joinedload (eager) or selectinload (subquery)
- **Connection pooling**: centralized, closed on shutdown
- **ORM ↔ Entity mapping**: in Repository (SoC)

## Logging (automatic in BaseRepository)

operation, table, query_type, duration_ms, found, entity_id. Slow queries → WARNING.

Full version: see [reference.md](reference.md)
