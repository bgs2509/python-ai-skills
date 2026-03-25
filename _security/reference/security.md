# Security

> Security at all levels — from input to logs. Secrets via environment variables (SSoT). For more on secrets management — see skill `_security` (_security/reference/secrets-management.md).

---

## Mandatory Rules

| Rule | Details |
|------|--------|
| Secrets only via environment variables | No hardcoded passwords, tokens, or API keys in code or git. SSoT — see skill `_security` (_security/reference/secrets-management.md). |
| .gitignore contains .env, *.pem, *.key, credentials.json | Checked automatically. Violation = blocker. |
| .env.example without real secrets | Only placeholders (CHANGE_ME). |
| Sensitive data sanitization in logs | Automatic masking via structlog processor (SSoT). See skill `_logging` (_logging/reference.md). |
| Validation at system boundaries | Input validation via Pydantic. Do not trust input data (Fail Fast). |
| Parameterized DB queries | SQL injection — blocker. See skill `_database` (_database/reference.md). |
| CORS configured (not `*` in production) | Explicit list of allowed origins. |
| Rate limiting for public endpoints | Protection against abuse. |
| HTTPS only in production | Unencrypted traffic is unacceptable. |
| Principle of least privilege | Each component has only the permissions it needs. |
| Pre-commit hooks | Automatic secret leak checking. See skill `_linters` (_linters/reference/linters.md). |
| Fail-fast configuration validation at startup | Required fields without defaults, format validation during Settings initialization. |

---

## OWASP Top 10 — Mandatory Checklist

Check for the absence of the following during every review:

| # | Vulnerability | How to prevent |
|---|--------------|----------------|
| 1 | Injection (SQL, OS, LDAP) | Parameterized queries, ORM |
| 2 | Broken Authentication | Secure password storage (bcrypt/argon2), sessions with timeout |
| 3 | Sensitive Data Exposure | Encryption in transit (HTTPS) and at rest, masking in logs |
| 4 | XML External Entities (XXE) | Disable external entities in XML parsers |
| 5 | Broken Access Control | Permission checks on every endpoint, deny by default |
| 6 | Security Misconfiguration | No default passwords, debug=False in production |
| 7 | Cross-Site Scripting (XSS) | Output escaping, Content-Security-Policy |
| 8 | Insecure Deserialization | Do not deserialize untrusted data, use Pydantic for validation |
| 9 | Using Components with Known Vulnerabilities | Regular dependency updates, safety check |
| 10 | Insufficient Logging | Centralized logging of all security events. See skill `_logging` (_logging/reference.md). |

---

## Docker Security

> See skill `_docker` (_docker/reference/docker.md) section "Security".
