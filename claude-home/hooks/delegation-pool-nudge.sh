#!/bin/bash
# PreToolUse hook (matcher: Task, an alias of the Agent tool): two soft hints at
# the moment a subagent is launched. The launch STILL runs; this never blocks.
#
# 1. Pool hint. The Agent tool can ONLY dispatch Anthropic models, so every
#    subagent spends the scarce pool. When the task being delegated looks
#    bulk/mechanical — the kind of work an external pool does acceptably —
#    remind the model that ~/.claude/scripts/model-run.sh exists and costs a
#    different quota.
# 2. Model hint (bd python-ai-skills-8of.4). A launch without `model` runs on
#    CLAUDE_CODE_SUBAGENT_MODEL or, for Explore, on the session model (measured
#    2026-10-13: Explore ignores the env var). List the work-type → model
#    mapping from the registry's `agent_work_types`, so the choice is explicit.
#    Model names are read from the registry at run time, never written here.
#
# Why a hook and not a rule in CLAUDE.md: CLAUDE.md is read at session start,
# so long-lived sessions never learn a newly added rule. Journals on 2026-09-22
# showed 14 of 17 active sessions predating the registry rule and zero subagent
# dispatches — the rule had no moment at which it could fire. A PreToolUse hook
# fires in already-running sessions, at the exact moment of delegation; 91 of
# 126 launches audited on 2026-10-13 happened outside any skill.
# Precedent and delivery mechanism: big-read-nudge.sh (bd python-ai-skills-bqi).
#
# Contract:
#   - stdin: JSON with tool_input.{description?, prompt?, subagent_type?, model?}
#   - env: MODEL_REGISTRY (default ~/.claude/model-registry.json)
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON only when hinting; empty otherwise
#   - PreToolUse stdout is NOT shown to the model, so the hint MUST be
#     delivered as additionalContext JSON, not plain echo.

set -euo pipefail

# Opt out entirely (e.g. while measuring a baseline).
[ "${DELEGATION_NUDGE:-on}" = "off" ] && exit 0

INPUT=$(cat 2>/dev/null) || exit 0   # unreadable stdin degrades to silence

echo "$INPUT" | REGISTRY="${MODEL_REGISTRY:-$HOME/.claude/model-registry.json}" python3 -c "
import json, os, re, sys

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

POOL_HINT = (
    'This Task will run on an Anthropic model — the Agent tool cannot reach any other pool, '
    'so it spends the scarce quota. The work you are delegating looks bulk/mechanical, which the '
    'executor or batch role handles acceptably at another pool\'s expense: '
    '\`~/.claude/scripts/model-run.sh --role executor --task <file> --out <file>\` '
    '(web research with sources: \`--role researcher\`; roles, fallback order and timeouts live in '
    '~/.claude/model-registry.json; every attempt is journalled). Dispatching the subagent anyway is '
    'fine when the work needs Anthropic-level judgement, when the result must come back into this '
    'conversation directly, or when the delegate needs tools the runner\'s one-shot call cannot give it.'
)


def mapping_lines(path):
    '''Work type -> model alias or runner role, from the registry; [] if unusable.'''
    try:
        reg = json.load(open(path))
        lines = []
        for e in reg['agent_work_types']['entries']:
            if 'tier' in e:
                alias = reg['models'][reg['tiers'][e['tier']]]['model_arg']
                lines.append(f'- {e[\"work\"]} → model \`{alias}\`')
            else:
                lines.append(f'- {e[\"work\"]} → \`~/.claude/scripts/model-run.sh --role {e[\"role\"]}\` (not the Agent tool)')
        return lines
    except Exception:
        return []


def model_hint(ti):
    kind = ti.get('subagent_type') or 'general-purpose'
    if ti.get('model') or kind == 'fork':
        return ''                    # explicit choice, or a fork that must share the parent cache
    if kind == 'Explore':
        head = ('This Explore subagent has no \`model\`: Explore runs on the session model, '
                'whatever CLAUDE_CODE_SUBAGENT_MODEL says.')
    elif kind == 'general-purpose':
        head = ('This subagent has no \`model\`: it runs on CLAUDE_CODE_SUBAGENT_MODEL, '
                'or on the session model when that is unset.')
    else:
        head = (f'This {kind} subagent has no \`model\` in the call: it runs on the model its agent '
                'definition sets, otherwise on CLAUDE_CODE_SUBAGENT_MODEL, otherwise on the session model.')
    lines = mapping_lines(os.environ['REGISTRY'])
    if not lines:
        return head + ' Pass \`model\` to match the work type (mapping: agent_work_types in ~/.claude/model-registry.json).'
    return head + ' Pass \`model\` to match the work type (registry agent_work_types):\n' + '\n'.join(lines)


try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)                      # malformed stdin degrades to silence

ti = d.get('tool_input', {}) or {}
text = ' '.join(str(ti.get(k, '') or '') for k in ('description', 'prompt'))
if not text.strip():
    sys.exit(0)

hints = []
if BULK.search(text) and not JUDGEMENT.search(text):
    hints.append(POOL_HINT)          # judgement wording wins over bulk wording
hint = model_hint(ti)
if hint:
    hints.append(hint)
if hints:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'additionalContext': '\n\n'.join(hints),
    }}))
" 2>/dev/null || true
exit 0
