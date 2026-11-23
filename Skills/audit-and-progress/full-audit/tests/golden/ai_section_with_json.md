## AI deep code analysis

```json
[
  {"file": "src/processor/m2_preproc.py", "line": 17, "severity": "critical", "check_id": "ai-spec-conflict", "rule_id": "fr-2-deduplication", "message": "FR-2 requires NFC normalisation before hash but m2 hashes raw text"},
  {"file": "src/shared/db/session.py", "line": 22, "severity": "middle", "check_id": "ai-security", "rule_id": "dsn-encoding", "message": "DSN built via string concat — special chars in password break parsing"}
]
```

### Critical
- **[critical]** `src/processor/m2_preproc.py:17` — FR-2 requires NFC normalisation before hash but m2 hashes raw text

### Middle
- **[middle]** `src/shared/db/session.py:22` — DSN built via string concat — special chars in password break parsing
