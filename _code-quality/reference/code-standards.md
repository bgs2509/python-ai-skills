# Code Standards

> Unified rules for writing code. Readability is more important than brevity (KISS). Project conventions are more important than personal preferences (CoC).

---

## Typing

- Type hints are MANDATORY for all parameters, return values, and class attributes (Explicit > Implicit)
- Modern syntax: `list[User]`, `dict[str, Any]`, `str | None` (not `Optional[str]`)
- Mypy configuration — see skill `_linters` (_linters/reference/linters.md)

---

## Docstrings (Google style)

- Mandatory for all public functions and classes
- Sections: Args, Returns, Raises, Examples (when needed)
- Private methods — docstring only if the logic is non-obvious

---

## Imports

- Only absolute imports (no relative imports)
- Grouping: standard library → third-party → local
- Alphabetical order within groups
- Automatic sorting — ruff (isort) — see skill `_linters` (_linters/reference/linters.md)

---

## Code Metrics

| Metric | Threshold | Principle |
|--------|-----------|-----------|
| Function length | ≤ 50 lines | KISS |
| Cyclomatic complexity | < 10 | KISS |
| Nesting depth | ≤ 4 levels | KISS |
| File length | < 500 lines | SRP |

---

## Async-First

- All I/O operations use async/await
- Synchronous blocking calls in async code — blocker
- For CPU-bound tasks — `asyncio.to_thread()` or ProcessPoolExecutor
