# Code Principles — Single Source of Truth

> The only place these principles are defined. Skills, agents, pipelines and review prompts
> point here; never restate a principle elsewhere (guard: `claude-home/hooks/test_principles_ssot.py`).
> Applies when planning, writing, reviewing and refactoring code. A violation is a blocker.

## Priority 1 — the least code that meets the requirement

1. **KISS** — the simplest code that works; readability over brevity and over cleverness.
   Violated when: function >50 lines; nesting >4; cyclomatic complexity ≥10; a layer, wrapper,
   factory, registry or base class with one implementation or one caller; a generic mechanism
   where a direct call does; three similar lines replaced by a premature abstraction.
2. **YAGNI** — build only what a current requirement (FR/NFR, contract, user request) needs.
   Violated when: a parameter, option, config key or flag with a single value in use; a method,
   branch or error path nobody calls or no input can reach; "for the future", "just in case",
   "for flexibility"; an unrequested feature; commented-out code; a backwards-compat shim for
   internal code.
3. **SSoT / DRY** — every fact (type, constant, config value, rule, logic) has one home; others
   reference it. Violated when: copy-paste; a constant or type defined twice; the same rule written
   in two documents.
4. **SOTA** — use the current documented API and pattern of each library (verified via Context7
   or official docs), not memory; "state of the art" means current and standard, not novel.
   Violated when: deprecated API, a hand-rolled version of what the stdlib or an already-used
   library provides, a new dependency for a few lines of code.

### Excess-code check (apply to every diff and every plan)

- **Deletion test:** if removing a function, branch, parameter or file breaks no test and no
  FR/contract, it is excess — delete it.
- **Trace test:** every new symbol traces to a named FR, NFR or contract item; no trace — excess.
- **Boundary test:** validation and defensive handling belong at system boundaries (user input,
  CLI arguments, external APIs, filesystem, network). A guard against a state that internal
  callers cannot produce is excess.
- **Precedence:** when principles conflict, KISS and YAGNI win. OCP, DIP and ISP justify an
  abstraction only when two real implementations or callers exist today.

## Priority 2 — structure

5. **SoC** — business logic apart from I/O; validation apart from processing. Violated when: a
   function mixes abstraction levels; a handler holds business logic.
6. **SRP** — one function, one task; one reason to change per class. Violated when: a name
   contains "and"; a class >500 lines; one requirement change edits several modules.
7. **OCP** — extend by adding, not by rewriting — once a second variant exists.
8. **LSP** — a subtype replaces its parent without changing the contract or raising new errors.
9. **ISP** — a client depends only on what it uses. Violated when: `NotImplemented` stubs; fat interfaces.
10. **DIP** — business logic depends on injected abstractions when a second implementation or a
    test double is needed now.
11. **LoD** — no reaching into another module's internals; no `a.b.c.d` chains.
12. **Composition > Inheritance** — inheritance only for is-a, depth ≤2–3.

## Priority 3 — correctness and clarity

13. **Fail Fast** — validate at entry, fail early with a clear message. Violated when: `except: pass`;
    a swallowed error; deep nesting instead of guard clauses.
14. **Explicit > Implicit** — type hints, named constants, visible side effects. Violated when:
    magic numbers; `*args/**kwargs` without need.
15. **CoC** — follow the project's existing conventions; a new style needs a reason.
16. **Testability** — dependencies injected, no hidden global state, deterministic functions.
17. **Security** — no secrets in code or logs; validated, parameterized input.
