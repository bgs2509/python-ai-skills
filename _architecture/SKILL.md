---
name: _architecture
description: >
  Python application architecture: DDD (layers, entities, Value Objects), Hexagonal (ports, adapters).
  Choosing between monolith and microservices. Use when designing project structure.
---

# Application Architecture

> Domain-Driven Design + Hexagonal Architecture. Domain is the single source of business rules (SSoT).

## Layers and Dependencies

```
api/ → application/ → domain/ ← infrastructure/
```

| Layer | Depends On | Contains |
|-------|-----------|----------|
| Domain | Nothing | Entities, Value Objects, domain services, interfaces |
| Application | Domain | Use Cases, Application Services, DTOs |
| API | Application | Controllers, middleware, HTTP schemas |
| Infrastructure | Domain | Repositories, HTTP clients, DB, cache |

**DIP**: Domain defines interfaces → Infrastructure implements them.

## Key Concepts

- **Entities**: unique identity, contain behavior (not anemic models)
- **Value Objects**: immutable, self-validating (Money, Email, Address)
- **Domain Services**: logic spanning multiple entities, stateless
- **Ports & Adapters**: inbound (Use Case) and outbound (Repository) ports
- **DI**: binding at the entry point (main.py / dependencies.py)

## Choosing: Monolith vs Microservices

| Criterion | Monolith | Microservices |
|-----------|----------|---------------|
| Team | 1-5 people | 5+ people |
| Stage | Early | Mature |
| Scaling | Unified | Independent |
| Deployment | Simple | Complex |

More details:
- DDD (layers, entities, Bounded Contexts): [reference/ddd.md](reference/ddd.md)
- Hexagonal (ports, adapters, structure): [reference/hexagonal.md](reference/hexagonal.md)
- Monolith: [reference/monolith.md](reference/monolith.md)
- Microservices: [reference/microservices.md](reference/microservices.md)
