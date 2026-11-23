# State schema — `docs/audit-loop/state.json`

Versioned in git. SSoT for the cycle.

```json
{
  "schema_version": 1,
  "prompt_version": 1,
  "started_at": "2026-04-30T12:00:00",
  "ended_at": null,
  "aborted": false,
  "max_rounds": 5,
  "current_round": 1,
  "context7_seen_libraries": ["aiogram@3.15.0", "..."],
  "rounds": [
    {
      "n": 1,
      "started_at": "ISO8601",
      "completed_at": "ISO8601 or null",
      "aborted_at": "ISO8601 or null",
      "interrupted_at": "ISO8601 or null",
      "git_tag_start": "audit-loop/R1/start",
      "codex_report": "docs/audit-loop/round-1.json",
      "codex_log": "docs/audit-loop/round-1.codex.log",
      "codex_exit_code": 0,
      "claude_decisions": "docs/audit-loop/round-1.md",
      "codex_summary": {"critical": 8, "medium": 7, "minor": 5},
      "auto_applied": [
        {
          "issue_id": "fnd-1",
          "fingerprint": "8-char-sha1",
          "module_id": "M-PREPROC",
          "category": "bug",
          "kind": "missing-await",
          "confidence": 82,
          "breakdown": {"context7": 20, "principles": 20, "precedent": 20, "graph": 12, "reversibility": 10},
          "evidence_links": ["src/foo.py:42", "https://..."],
          "commit_sha": "abc1234",
          "applied_at": "ISO8601"
        }
      ],
      "asked": [
        {"issue_id": "fnd-12", "fingerprint": "...", "confidence": 55,
         "qa_question": "...", "qa_options": ["...", "..."],
         "qa_user_choice": "...", "qa_rationale": "...", "commit_sha": "..."}
      ],
      "deferred": [
        {"issue_id": "fnd-9", "fingerprint": "...", "adr": "docs/adr/ADR-NNN-*.md"}
      ],
      "still_open": [{"issue_id": "fnd-3", "fingerprint": "..."}],
      "stagnation_with_prev": false,
      "stagnation_reasoning": null,
      "category_penalties": {"bug": 0, "principle": -20},
      "hooks": {"pre_commit": "pass", "grace_refresh": "pass", "grace_lint": "pass"},
      "duration_seconds": 442
    }
  ]
}
```

**Invariants:**
- `fingerprint = sha1(module_id|category|kind)[:8]` — canonical issue identity across rounds.
- Every `rounds[N]` entry has either `completed_at` (success) or `aborted_at` (skipped/manually closed).
- `prompt_version` frozen on R1 from `config.toml.codex_prompt_version`. Mismatch on R{N>1} → ERROR, abort.
