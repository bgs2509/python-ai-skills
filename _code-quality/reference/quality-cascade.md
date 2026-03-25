# Quality Cascade — 17 Quality Principles

> **All 17 principles apply ALWAYS** — when writing code, during review, and while refactoring. Violating any principle is a blocker.

---

## Foundational Principles

| # | Principle | Essence | Red Flags |
|---|-----------|---------|-----------|
| 1 | **DRY** | Do not duplicate code. Shared logic goes into reusable modules. | Copy-paste between files; identical logic in different places; constants defined twice. |
| 2 | **KISS** | Simple solutions without over-engineering. Readability is more important than brevity. | Function > 50 lines; nesting > 4 levels; cyclomatic complexity > 10; abstraction for the sake of abstraction. |
| 3 | **YAGNI** | Implement only what is needed. No code "for the future." | Methods "just in case"; parameters without current usage; commented-out code; abstractions without clients. |
| 4 | **SoC** | Separate concerns. Business logic separate from I/O, validation separate from processing. | Function mixes abstraction levels; controller contains business logic; one file covers multiple topics. |
| 5 | **SSoT** | Each data type is defined in one place. Configuration is in settings. | Constants duplicated; types defined in multiple modules; config scattered across files. |
| 6 | **CoC** | Follow project conventions. Minimize new rules. | Naming is inconsistent; structure differs from existing patterns; new style without justification. |
| 7 | **Security** | Security at all levels — from input to logs. | Hardcoded secrets; missing validation; logging passwords; SQL without parameterization. |

---

## SOLID

| # | Principle | Essence | Red Flags |
|---|-----------|---------|-----------|
| 8 | **SRP** | One function — one task. One responsibility per class. | Name contains "and" (do_x_and_y); class > 500 lines; God objects; changing a requirement breaks multiple modules. |
| 9 | **OCP** | Open for extension, closed for modification. | Adding a variant requires rewriting; long if/elif chains; breaking changes on extension. |
| 10 | **LSP** | Subtypes fully replace parent types. | Subclass throws exceptions the parent does not; overridden method changes the contract. |
| 11 | **ISP** | Small, specific interfaces. A client depends only on what it uses. | Fat interfaces; NotImplemented stubs; client uses 2 out of 10 methods. |
| 12 | **DIP** | Depend on abstractions, not on concrete implementations. Dependency injection. | Direct import of a concrete class in business logic; unable to replace a dependency for tests; hardcoded dependencies. |

---

## Additional Principles

| # | Principle | Essence | Red Flags |
|---|-----------|---------|-----------|
| 13 | **LoD** | Minimal coupling. A module does not reach into the internals of another. | Call chains a.b.c.d; accessing internal structures; excessive imports. |
| 14 | **Fail Fast** | Validate at the input, fail explicitly and early with a clear message. | `except: pass`; silent errors; deep nesting instead of guard clauses; unclear messages. |
| 15 | **Explicit > Implicit** | Explicit code without magic. Type hints, named constants, documented side effects. | Magic numbers; `*args/**kwargs` without necessity; hidden side effects; missing type hints. |
| 16 | **Composition > Inheritance** | Prefer composition. Inheritance only for is-a, depth ≤ 2-3. | Deep hierarchies; multiple inheritance (except mixins); diamond problem. |
| 17 | **Testability** | Code can be tested in isolation. Dependencies are injected, no global state. | Cannot write a unit test without complex setup; global state; non-deterministic functions. |

---

## Centralization (SSoT + DRY)

The following aspects MUST be centralized — defined in one place:

| Aspect | Where it is defined | Red Flag |
|--------|-------------------|----------|
| Configuration | `core/config.py` (Pydantic Settings) | Config scattered across files |
| Logging | `core/logging.py` (structlog) | Each module configures logging differently |
| Error handling | `core/exceptions.py` + single handler | Duplicated try/except blocks in different modules |
| Dependency Injection | `api/dependencies.py` | Dependencies created in different places |
| Validation | Pydantic schemas at system boundaries | Validation in business logic instead of the input layer |

---

## Where Principles are Detailed

| Principle | File |
|-----------|------|
| DIP, SoC, SRP (layer architecture) | skill `_architecture` (_architecture/reference/ddd.md, architecture/reference/hexagonal.md) |
| SSoT, DRY (logging) | skill `_logging` (_logging/reference.md) |
| SSoT, DRY (error handling) | skill `_error-handling` (_error-handling/reference.md) |
| SSoT, DIP (database) | skill `_database` (_database/reference.md) |
| CoC (naming) | skill `_code-quality` (_code-quality/reference/naming.md) |
| KISS, Explicit (code standards) | skill `_code-quality` (_code-quality/reference/code-standards.md) |
| Security | skill `_security` (_security/reference/security.md) |
| Testability | skill `_testing` (_testing/reference.md) |
