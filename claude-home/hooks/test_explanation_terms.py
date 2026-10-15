"""Tests for explanation-terms.py — Stop hook that flags coined Latin terms in Russian prose.

A coined term (a compound the model glued together on the fly, e.g. `read-nudge`) leaves no
trace in the session, the instruction files or the repository. The hook asks for one
correction line per such word through Stop `additionalContext`; it never blocks the turn,
because a block makes the model rewrite an answer the user has already read (bd
python-ai-skills-r1f.1).
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "explanation-terms.py"

# Russian filler so the message passes the Russian-prose filter (>=200 letters, >=30% Cyrillic).
PROSE = (
    "Это длинный русский абзац, который нужен только для того, чтобы хук признал сообщение "
    "русским текстом и начал искать в нём латинские слова. Он описывает работу проверки "
    "простыми словами и не несёт другого смысла. "
) * 2


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    (path / ".claude").mkdir(parents=True)
    return path


@pytest.fixture
def workdir(tmp_path):
    path = tmp_path / "work"
    path.mkdir()
    return path


def transcript(tmp_path, events):
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events))
    return path


def user_text(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result(text):
    return {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "content": text}]},
    }


def assistant_text(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def run(home, workdir, message, events=(), tmp_path=None, in_transcript=True, **extra):
    events = list(events) + ([assistant_text(message)] if in_transcript else [])
    payload = {
        "hook_event_name": "Stop",
        "last_assistant_message": message,
        "cwd": str(workdir),
        "transcript_path": str(transcript(tmp_path, events)),
        **extra,
    }
    return subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=workdir,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


def feedback(result):
    out = json.loads(result.stdout)
    assert "decision" not in out
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    return out["hookSpecificOutput"]["additionalContext"]


def test_reads_the_final_message_from_last_assistant_message(home, workdir, tmp_path):
    # The transcript holds no assistant message at all, as can happen at Stop time.
    result = run(home, workdir, PROSE + "Слово read-nudge здесь.", [user_text("вопрос")], tmp_path,
                 in_transcript=False)
    assert result.returncode == 0
    assert "read-nudge" in feedback(result)


def test_coined_word_gets_one_line_correction_request_not_a_block(home, workdir, tmp_path):
    result = run(home, workdir, PROSE + "Слово read-nudge здесь.", [], tmp_path)
    context = feedback(result)
    assert "«read-nudge»" in context
    assert "Поправка к термину" in context


@pytest.mark.parametrize("token", ["foo_bar_baz", "qwen38-lil-low", "`dangerouslyDisableSandbox`"])
def test_identifier_shapes_are_not_candidates(home, workdir, tmp_path, token):
    result = run(home, workdir, PROSE + f"Имя {token} здесь.", [], tmp_path)
    assert result.stdout == ""


def test_compound_with_a_product_name_inside_is_still_a_candidate(home, workdir, tmp_path):
    # Three of the 37 coined words in blocks.jsonl glue a camel-cased product name into a compound.
    result = run(home, workdir, PROSE + "Схема reverse-WireGuard здесь.", [], tmp_path)
    assert "«reverse-WireGuard»" in feedback(result)


def test_word_broken_by_a_line_wrap_after_a_hyphen_is_found(home, workdir, tmp_path):
    wrapped = "path claude-home/housekeeping/claude-housekeeping-\n      task.md"
    result = run(home, workdir, PROSE + "Файл claude-housekeeping-task здесь.", [tool_result(wrapped)], tmp_path)
    assert result.stdout == ""


def test_word_present_in_a_repository_file_is_real(home, workdir, tmp_path):
    (workdir / "notes.md").write_text("the drift-guard compares renders\n")
    subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
    subprocess.run(["git", "add", "notes.md"], cwd=workdir, check=True)
    result = run(home, workdir, PROSE + "Проверка drift-guard здесь.", [], tmp_path)
    assert result.stdout == ""


def test_silent_when_already_continuing_after_a_stop_hook(home, workdir, tmp_path):
    result = run(home, workdir, PROSE + "Слово read-nudge здесь.", [], tmp_path, stop_hook_active=True)
    assert result.stdout == ""


def test_english_text_is_not_checked(home, workdir, tmp_path):
    message = "This English answer mentions read-nudge and many other words. " * 5
    result = run(home, workdir, message, [], tmp_path)
    assert result.stdout == ""
