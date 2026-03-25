# Monolithic Architecture Specifics

> All components run in a single process. Internal structure follows DDD/Hexagonal (see skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md)) — same layers, same isolation.

---

## When a Monolith is the Right Choice

- Small team (1-5 developers)
- Early stage of the project — the domain is not yet well-defined
- No need for independent scaling of components
- Deployment simplicity is more important than flexibility

---

## Module Boundaries

- Separation by Bounded Contexts within a single process
- Each module has its own structure: domain/, application/, infrastructure/
- Modules interact through public interfaces, not through internal classes (LoD)

```
src/
├── users/                   # Users module
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── orders/                  # Orders module
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── core/                    # Shared: config, logging, exceptions (SSoT)
├── api/                     # Unified API layer
└── main.py
```

---

## Shared Database

- Single DB, separation by schemas or table prefixes
- Each module accesses ONLY its own tables through its own Repository (SSoT)
- Direct access to another module's tables is prohibited — only through its Application Service (SoC)
- Migrations: single Alembic, but migrations are grouped by module

---

## Internal Calls

- Direct imports through interfaces (DIP), not through HTTP
- Module A calls Module B's Application Service, not its Repository directly (LoD)
- Single exception handler for the entire application (SSoT, DRY)
- Single logging configuration (SSoT, DRY)

---

## Modular Monolith (Preparation for Split)

- If modules respect boundaries — splitting into microservices is minimally painful
- Replacing direct calls with HTTP calls
- Replacing shared DB with separate DBs
- Readiness indicator for split: modules have no circular dependencies

---

## Risks and Anti-patterns

| Risk | Description | How to avoid |
|------|-------------|-------------|
| God object | A single class/module knows about everything | SRP — single responsibility |
| Circular dependencies | Module A → B → A | DIP — extract an interface |
| Shared mutable state | Global variables between modules | SSoT — state in one place |
| Missing boundaries | Modules directly import each other's internals | LoD — only public interfaces |
| Single point of failure | One module crash brings down everything | Error isolation, graceful degradation |
