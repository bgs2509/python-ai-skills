# Naming Conventions

> Uniformity is more important than personal preferences (CoC). Names should be explicit and descriptive (Explicit > Implicit).

---

## Python

| Element | Style | Example |
|---------|-------|---------|
| Module/file | snake_case | `user_service.py` |
| Class | PascalCase | `UserService`, `OrderRepository` |
| Function/method | snake_case | `get_user_by_id()` |
| Variable | snake_case | `user_name`, `is_active` |
| Constant | UPPER_SNAKE | `MAX_RETRIES`, `DEFAULT_PAGE_SIZE` |
| Private | _prefix | `_internal_method()` |
| Exception | PascalCase + Error | `NotFoundError`, `ValidationError` |
| Pydantic schema | PascalCase | `UserCreate`, `UserResponse` |
| DTO | PascalCase + DTO | `CreateUserDTO`, `UserDTO` |

---

## Naming Patterns by Layer

| Layer | Pattern | Example |
|-------|---------|---------|
| Domain Entity | Noun | `User`, `Order`, `Payment` |
| Value Object | Concept | `Money`, `Email`, `DateRange` |
| Repository | Entity + Repository | `UserRepository`, `OrderRepository` |
| Application Service | Action + Service | `UserService`, `PaymentService` |
| Use Case | Verb + Noun | `CreateUser`, `ProcessPayment` |
| API Router | Plural | `/users`, `/orders` |
| Middleware | Purpose + Middleware | `RequestLoggingMiddleware` |

---

## Service Naming (microservices)

- By Bounded Context: `user-service`, `order-service`
- Format: kebab-case for service names
- Docker: `{context}-api`, `{context}-data`
- Environment variables: `{CONTEXT}_API_URL`

---

## Anti-patterns

| Bad | Good | Why |
|-----|------|-----|
| `data`, `info`, `temp` | `user_data`, `order_info` | Uninformative (Explicit) |
| `do_stuff()` | `send_notification()` | Does not describe the action |
| `Manager`, `Handler` (without context) | `UserService`, `PaymentProcessor` | Too generic |
| `utils.py` (junk drawer) | Specific modules by purpose | Violates SRP |
| `process()` | `validate_order()` | Hides intent |
