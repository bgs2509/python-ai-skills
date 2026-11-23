# Domain-Driven Design (DDD)

> Organizing code around the business domain. Domain is the single source of business rules (SSoT).

---

## Layers and Dependency Direction

```
api/ → application/ → domain/ ← infrastructure/
```

| Layer | Depends on | Contains |
|-------|-----------|----------|
| **Domain** | Nothing | Entities, Value Objects, domain services, repository interfaces |
| **Application** | Domain | Use Cases, Application Services, DTO |
| **API** | Application, Domain | Controllers/routers, middleware, HTTP schemas |
| **Infrastructure** | Application, Domain | Repository implementations, HTTP clients, DB, cache |

**Principle (DIP)**: Domain defines interfaces. Infrastructure implements them. Domain never depends on Infrastructure.

---

## Entities

- Have unique identity (id)
- Contain behavior, not just data (SRP — anemic models are prohibited)
- Encapsulate business rules and invariants
- Validate their state on creation and modification (Fail Fast)

**Red flags**:
- Entity without methods — only fields (anemic model)
- Business logic in services that should be in the entity
- Direct modification of fields from outside without validation

---

## Value Objects

- Have no identity — compared by value
- Immutable — cannot be changed after creation
- Self-validating — impossible to create an invalid object (Fail Fast)
- Examples: Money, Email, Address, DateRange

**Rules**:
- If a concept has no identity — it is a Value Object
- Value Object is defined in Domain (SSoT)
- Reused across all layers (DRY)

---

## Domain Services

- Logic that does not belong to a single entity
- Coordination between multiple entities
- Stateless
- Defined in Domain

**When to use**: an operation involves multiple entities and cannot belong to any single one.

---

## Repository Interfaces

- Interface is defined in Domain (DIP)
- Implementation — in Infrastructure
- Repository is the single point of data access for each entity (SSoT)
- Business logic NEVER accesses the DB directly (SoC)

```
domain/
    repositories/
        user_repository.py          # Interface (ABC)

infrastructure/
    database/
        user_repository_impl.py     # Implementation
```

---

## Dependency Graph

- Explicit, directed, acyclic
- If A depends on B, then B CANNOT depend on A
- Circular dependency — architectural blocker
- Resolving cycles: extracting an interface into Domain (DIP) or creating a new module

---

## Bounded Contexts

- Each context has its own domain model
- The same concept may have different representations in different contexts
- Contexts interact through explicit interfaces (Anti-Corruption Layer)
- In a monolith — separation by modules, in microservices — by services
