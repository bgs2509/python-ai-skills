#!/bin/bash
# PreToolUse hook (matcher: Task): soft nudge to consider a cheaper pool.
#
# The Agent tool can ONLY dispatch Anthropic models, so every subagent spends
# the scarce pool. When the task being delegated looks bulk/mechanical — the
# kind of work an external pool does acceptably — remind the model that
# ~/.claude/scripts/model-run.sh exists and costs a different quota. The Task
# STILL runs; this never blocks.
#
# Why a hook and not a rule in CLAUDE.md: CLAUDE.md is read at session start,
# so long-lived sessions never learn a newly added rule. Journals on 2026-09-22
# showed 14 of 17 active sessions predating the registry rule and zero subagent
# dispatches — the rule had no moment at which it could fire. A PreToolUse hook
# fires in already-running sessions, at the exact moment of delegation.
# Precedent and delivery mechanism: big-read-nudge.sh (bd python-ai-skills-bqi).
#
# Contract:
#   - stdin: JSON with tool_input.{description?, prompt?, subagent_type?, model?}
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON only when nudging; empty otherwise
#   - PreToolUse stdout is NOT shown to the model, so the nudge MUST be
#     delivered as additionalContext JSON, not plain echo.

set -euo pipefail

# Opt out entirely (e.g. while measuring a baseline).
[ "${DELEGATION_NUDGE:-on}" = "off" ] && exit 0

INPUT=$(cat)

VERDICT=$(echo "$INPUT" | python3 -c "
import json, re, sys

# Work that an external pool handles acceptably: bulk reading, inventory,
# mechanical edits, drafting from a finished spec. Deliberately narrow — a
# nudge on design or review work would be noise, since those need the
# strongest model and the quality axis was never measured.
BULK = re.compile(
    r'\b('
    r'grep|inventor|enumerat|catalog|sweep|scan|audit\s+all|list\s+all|'
    r'find\s+all|search\s+(?:for|across|through)|read\s+(?:all|every|each)|'
    r'bulk|mass|mechanical|rename|reformat|boilerplate|scaffold|'
    r'draft\s+(?:docs|tests|documentation)|summar[iy]'
    r')', re.I)

# Work that must stay on the strong pool regardless of volume.
JUDGEMENT = re.compile(
    r'\b('
    r'design|architect|contract|review|decide|choose\s+between|trade-?off|'
    r'security|debug|root\s+cause|refactor\s+the\s+architecture'
    r')', re.I)

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)                      # malformed stdin degrades to silence

ti = d.get('tool_input', {}) or {}
text = ' '.join(str(ti.get(k, '') or '') for k in ('description', 'prompt'))
if not text.strip():
    sys.exit(0)

if JUDGEMENT.search(text):
    sys.exit(0)                      # judgement work: stay on Anthropic, say nothing
if not BULK.search(text):
    sys.exit(0)                      # not obviously bulk: say nothing

print('nudge')
" 2>/dev/null || echo "")

[ "${VERDICT:-}" = "nudge" ] || exit 0

REASON="This Task will run on an Anthropic model — the Agent tool cannot reach any other pool, so it spends the scarce quota. The work you are delegating looks bulk/mechanical, which the executor or batch role handles acceptably at another pool's expense: \`~/.claude/scripts/model-run.sh --role executor --task <file> --out <file>\` (roles, fallback order and timeouts live in ~/.claude/model-registry.json; every attempt is journalled). Dispatching the subagent anyway is fine when the work needs Anthropic-level judgement, when the result must come back into this conversation directly, or when the delegate needs tools the runner's one-shot call cannot give it."

REASON="$REASON" python3 -c "
import json, os
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'additionalContext': os.environ['REASON'],
    }
}))
"
exit 0
