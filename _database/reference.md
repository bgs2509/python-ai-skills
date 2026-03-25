# Database

> Repository is the single point of data access (SSoT, DIP). Business logic NEVER accesses the DB directly (SoC).

---

## Repository Pattern

- Interface is defined in Domain (ABC/Protocol) — DIP
- Implementation — in Infrastructure
- One Repository per entity (SRP)
- Repository returns domain entities, not ORM models
- Base Repository with common operations (CRUD) — DRY

### Base Repository (DRY)

Common operations are defined once in the base class:
- `get_by_id(id) -> Entity | None`
- `get_all(filters, pagination) -> list[Entity]`
- `create(entity) -> Entity`
- `update(entity) -> Entity`
- `delete(id) -> None`

Specific operations — in concrete Repositories:
- `UserRepository.get_by_email(email) -> User | None`
- `OrderRepository.get_by_status(status) -> list[Order]`

---

## Migrations (Alembic)

- Alembic as the sole migration tool (SSoT)
- Auto-generation: `alembic revision --autogenerate -m "description"`
- Each migration is atomic and reversible (downgrade)
- Naming: `{number}_{description}.py`
- Migrations are stored in git
- Manual DB changes in production are prohibited — only through migrations

---

## Connection Pooling

- Connection pool is configured centrally (SSoT)
- Parameters: pool_size, max_overflow, pool_timeout, pool_recycle
- Connections closed on graceful shutdown
- Monitoring: count of active/waiting connections

---

## Parameterized Queries

- SQL injection — blocker
- Always use parameterized queries (SQLAlchemy bindparams)
- No string formatting for SQL
- ORM is preferred over raw SQL

---

## Transactions

- Explicit transaction boundaries — in Application Service (SoC)
- Repository does not manage transactions — that is the responsibility of the Application layer
- Unit of Work pattern for consistent operations
- Compensating transactions for rollbacks in distributed systems

---

## N+1 Problem

- Detection: WARNING in logs when > N queries to the same table per request
- Solution: joinedload (eager loading) or selectinload (subquery)
- Rule: for relations that are always needed — joinedload, for optional ones — selectinload
- Monitor query count per request

---

## DB Operation Logging (DRY)

Logging is implemented in the base Repository — automatically for all operations:

| Field | Description |
|-------|-------------|
| operation | create/read/update/delete |
| table | Table name |
| query_type | SELECT/INSERT/UPDATE/DELETE |
| duration_ms | Execution time |
| found | Whether the record was found (for SELECT) |
| entity_id | Entity ID |

Slow queries (> threshold) — WARNING.

> For more on the logging format — see skill `_logging` (_logging/reference.md).

---

## ORM Models vs Domain Entities

- ORM models — in Infrastructure (tied to the DB)
- Domain Entities — in Domain (pure business logic)
- ORM ↔ Entity mapping — in Repository (SoC)
- ORM models do not leak above the Infrastructure layer
