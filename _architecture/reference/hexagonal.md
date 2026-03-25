# Hexagonal Architecture (Ports & Adapters)

> Business logic is isolated from the outside world through ports (interfaces) and adapters (implementations). Replacing an adapter does not require changes to business logic (OCP, DIP).

---

## Dependency Direction

```
api/ → application/ → domain/ ← infrastructure/
```

All dependencies point INWARD — toward Domain. Domain knows nothing about the outside world.

---

## Ports and Adapters

### Ports (interfaces)

- Defined in Domain or Application (SSoT)
- Describe WHAT is needed, not HOW
- Abstract base classes (ABC) or Protocol

| Type | Direction | Example |
|------|-----------|---------|
| **Inbound port** | Outside world → Application | Use Case interface |
| **Outbound port** | Application → Outside world | Repository interface, HTTP client interface |

### Adapters (implementations)

- Implement ports with a specific technology
- Defined in Infrastructure or API
- Easily replaceable (OCP — open for extension)

| Type | Layer | Example |
|------|-------|---------|
| **Inbound adapter** | API | FastAPI router, CLI command, Event handler |
| **Outbound adapter** | Infrastructure | PostgreSQL repository, Redis cache, httpx client |

---

## Dependency Injection

- Binding ports to adapters — at the entry point (main.py or dependencies.py)
- Single place for dependency configuration (SSoT)
- Allows replacing adapters for tests (Testability)

**Rules**:
- Business logic depends on the interface, not the implementation (DIP)
- Direct import of a concrete class in business logic — blocker
- Inability to replace a dependency for tests — blocker

---

## Directory Structure

```
src/
├── api/                     # Inbound adapters (HTTP)
│   ├── v1/                  # API versioning
│   └── dependencies.py      # Dependency Injection (SSoT for bindings)
├── application/             # Use Cases
│   ├── services/            # Application Services
│   └── dtos/                # Data Transfer Objects
├── domain/                  # Pure business logic (depends on NOTHING)
│   ├── entities/            # Entities with identity
│   ├── value_objects/       # Value objects (immutable)
│   ├── services/            # Domain services
│   └── repositories/        # Repository interfaces (ABC)
├── infrastructure/          # Outbound adapters
│   ├── database/            # Repository implementations
│   ├── http/                # HTTP clients to external APIs
│   └── cache/               # Cache
├── schemas/                 # Pydantic API schemas
├── core/                    # Configuration, logging, exceptions
│   ├── config.py            # Settings (SSoT for configuration)
│   ├── logging.py           # Centralized logging (SSoT)
│   └── exceptions.py        # Exception hierarchy (SSoT)
└── main.py                  # Entry point
```

---

## Benefits

| Property | How it is achieved |
|----------|-------------------|
| Testability | Replacing adapters with mocks via DI |
| Flexibility | Changing DB/cache/API without modifying business logic |
| Isolation | Domain does not depend on frameworks or libraries |
| Readability | Clear separation of concerns (SoC) |
