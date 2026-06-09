---
name: _security
description: >
  Python application security: OWASP Top 10 checklist, validation, CORS, rate limiting,
  secrets management (Pydantic Settings, .env.example).
  TRIGGER when: security review/audit, OWASP Top 10 check, input validation, CORS/rate limiting,
  secrets management (.env.example, Pydantic Settings).
  SKIP when: general code-quality review (use _code-quality), Bandit/linter setup (use _linters),
  app exception design (use _error-handling).
---

# Security

> Security at all levels — from input to logs. Secrets via environment variables (SSoT).

## Mandatory Rules

| Rule | Details |
|------|---------|
| Secrets only via env vars | No hardcoded passwords, tokens, or API keys |
| .gitignore | .env, *.pem, *.key, credentials.json |
| .env.example without secrets | Only CHANGE_ME placeholders |
| Log sanitization | Automatic masking via structlog |
| Validation at boundaries | Pydantic, Fail Fast |
| Parameterized SQL | SQL injection is a blocker |
| CORS (no `*` in prod) | Explicit list of origins |
| Rate limiting | For public endpoints |
| HTTPS only in prod | Unencrypted traffic is unacceptable |
| Pre-commit hooks | Automatic secret leak detection |

## OWASP Top 10

| # | Vulnerability | Prevention |
|---|--------------|------------|
| 1 | Injection | Parameterized queries, ORM |
| 2 | Broken Auth | bcrypt/argon2, sessions with timeout |
| 3 | Sensitive Data | HTTPS, masking in logs |
| 4 | XXE | Disable external entities |
| 5 | Broken Access | Permission checks, deny by default |
| 6 | Misconfiguration | No default passwords, debug=False |
| 7 | XSS | Escaping, CSP |
| 8 | Insecure Deserialization | Pydantic for validation |
| 9 | Known Vulnerabilities | Dependency updates |
| 10 | Insufficient Logging | Logging security events |

Secrets management (Pydantic Settings, rotation): see [reference/secrets-management.md](reference/secrets-management.md)
Full security rules: see [reference/security.md](reference/security.md)
