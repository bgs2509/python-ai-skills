"""Tests for glossary.py — per-project synonym glossary: memo (UserPromptSubmit), stop (Stop), --staged (pre-commit).

A project keeps one `## Glossary` section in its AGENTS.md: one bullet per group of forbidden
synonyms with one canonical term. The memo delivers it before the answer, the Stop mode asks
for a one-line correction per forbidden form, the pre-commit mode refuses a commit that adds
one (bd python-ai-skills-du5). Isolation as in test_explanation_terms.py: a fake HOME and a
temporary git repository per test; fixtures are inline strings.
"""

import json
import subprocess
from pathlib import Path

import pytest

import glossary

HOOK = Path(__file__).resolve().parent / "glossary.py"
REPO = HOOK.parents[2]


def section_of(body):
    return glossary.cut_section("# Project\n\n## Glossary\n\n" + body + "\n", "test")


def parse(body):
    return glossary.parse_section(section_of(body), "test")


@pytest.mark.parametrize(
    ("line", "forms", "canonical"),
    [
        ("- «a», «b», «c d» → **term** — def text (English: x y)", ("a", "b", "c d"), "term"),
        ("- **solo** — only a definition", (), "solo"),
        ("- «реестр», «регистр» → **таблица**", ("реестр", "регистр"), "таблица"),
        ("- «TP (в значении параллелизма)», «амортизированно O(1)» → **x**", ("TP (в значении параллелизма)", "амортизированно O(1)"), "x"),
        ("* «a» → **b** — star bullet (источник: решение 2026-10-20)", ("a",), "b"),
    ],
)
def test_entry_line_parses(line, forms, canonical):
    groups, exceptions, pointer = parse(line)
    assert [(g.forms, g.canonical, g.line) for g in groups] == [(forms, canonical, line)]
    assert (exceptions, pointer) == ((), None)


@pytest.mark.parametrize(
    "line", ["- «x» → канонический без звёздочек", "- Исключение: «форма» без источника", "- просто пункт"]
)
def test_bullet_that_matches_no_form_is_a_contract_error(line):
    with pytest.raises(glossary.GlossaryError, match="matches no glossary form"):
        parse(line)


def test_exception_line_carries_a_source():
    groups, exceptions, _ = parse("- Исключение: «реестр моделей» — источник: model-registry.json")
    assert (groups, exceptions) == ((), ("реестр моделей",))


def test_prose_blank_lines_and_fenced_examples_are_skipped():
    body = "Проза без маркера.\n\n```text\n- «x» → без звёздочек\n```\n\n- «a» → **b**"
    groups, _, pointer = parse(body)
    assert [g.canonical for g in groups] == ["b"] and pointer is None


def test_only_the_example_block_gives_zero_groups():
    assert parse("```text\n- «a» → **b**\n```") == ((), (), None)


def test_section_ends_at_the_next_heading_of_any_level():
    text = "## Glossary\n\n- «a» → **b**\n\n### Exceptions\n\n- «c» → **d**\n"
    groups, _, _ = glossary.parse_section(glossary.cut_section(text, "t"), "t")
    assert [g.canonical for g in groups] == ["b"]


def test_two_glossary_headings_are_a_contract_error():
    with pytest.raises(glossary.GlossaryError, match="more than one"):
        glossary.cut_section("## Glossary\n\n- «a» → **b**\n\n## Glossary\n", "t")


def test_no_heading_means_no_section():
    assert glossary.cut_section("# T\n\n## Other\n\ntext\n", "t") is None


def test_single_pointer_line_is_a_pointer_with_blank_lines_allowed():
    assert parse("\nGlossary file: `glossary.md`\n\n") == ((), (), "glossary.md")


def test_pointer_line_among_prose_is_prose():
    groups, _, pointer = parse("Раздел больше 200 строк — одна строка:\nGlossary file: `glossary.md`")
    assert (groups, pointer) == ((), None)


def test_ml_sobes_form_fixture_of_twelve_rows():
    rows = "\n".join([
        "- «one-hot», «прямое кодирование» → **one-hot кодирование** — Вектор из нулей с единицей (English: one-hot encoding)",
        "- **таблица** — Данные в строках и столбцах (English: table)",
        "- «OOF» → **out-of-fold** — Признак по данным без объекта (English: out-of-fold)",
        "- «K» → **ключ** — Вектор ключа внимания (English: key)",
        "- «TP (в значении параллелизма)» → **тензорный параллелизм** — Разбиение слоя (English: tensor parallelism)",
        "- **precision** — Доля верных среди найденных (English: precision)",
        "- «пересэмплирование», «увеличение миноритарного класса» → **oversampling** — Дублирование (English: oversampling)",
        "- **recall@k** — Полнота в первых k (English: recall at k)",
        "- «амортизированно O(1)» → **амортизированная константа** — Средняя стоимость (English: amortized constant)",
        "- «фича» → **признак** — Столбец данных (English: feature)",
        "- **SMOTE** — Синтетические объекты (English: SMOTE)",
        "- «базовая модель» → **эталонная модель** — Модель для сравнения (English: baseline)",
    ])
    groups, _, _ = parse(rows)
    assert len(groups) == 12
    assert sum(len(g.forms) for g in groups) == 10


def sh(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    (path / ".claude").mkdir(parents=True)
    return path


def make_project(tmp_path, files, git=True):
    root = tmp_path / "project"
    root.mkdir()
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    if git:
        sh(root, "init", "-q")
    return root


GLOSSARY_MD = "# Project\n\n## Glossary\n\n- «фича» → **признак** — столбец данных\n- «лог» → **журнал**\n"


def test_lookup_reads_agents_md_at_the_root(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD})
    found = glossary.load_glossary(root)
    assert [g.canonical for g in found.groups] == ["признак", "журнал"]
    assert (found.path, found.pointed) == (str(root / "AGENTS.md"), False)


def test_lookup_falls_back_to_claude_md_and_prefers_agents_md(tmp_path):
    only_claude = make_project(tmp_path, {"CLAUDE.md": GLOSSARY_MD})
    assert glossary.load_glossary(only_claude).path == str(only_claude / "CLAUDE.md")
    both = tmp_path / "both"
    both.mkdir()
    (both / "AGENTS.md").write_text("# P\n\nno glossary here\n")
    (both / "CLAUDE.md").write_text(GLOSSARY_MD)
    assert glossary.load_glossary(both) is None  # the first regular file wins, even without a glossary


def test_lookup_skips_a_directory_named_like_an_instruction_file(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md/keep": "x", "CLAUDE.md": GLOSSARY_MD})
    assert glossary.load_glossary(root).path == str(root / "CLAUDE.md")


@pytest.mark.parametrize("files", [{}, {"AGENTS.md": "# P\n\n## Other\n\ntext\n"}])
def test_no_instruction_file_or_no_heading_means_no_glossary(tmp_path, files):
    assert glossary.load_glossary(make_project(tmp_path, files)) is None


def test_relative_pointer_reads_the_pointed_file(tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "# P\n\n## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "# G\n\nheader\n\n" + GLOSSARY_MD.split("# Project\n\n")[1] + "\n## Спорные выборы\n\n1. проза\n",
    })
    found = glossary.load_glossary(root)
    assert found.pointed and found.path == str(root / "glossary.md")
    assert [g.canonical for g in found.groups] == ["признак", "журнал"]


def test_absolute_pointer_reaches_another_domain(tmp_path):
    shared = tmp_path / "shared.md"
    shared.write_text(GLOSSARY_MD)
    root = make_project(tmp_path, {"AGENTS.md": f"## Glossary\n\nGlossary file: `{shared}`\n"})
    assert glossary.load_glossary(root).path == str(shared)


@pytest.mark.parametrize(
    ("pointed", "reason"),
    [(None, "unreadable"), ("# G\n\nno heading\n", "no '## Glossary' heading"), ("## Glossary\n\nGlossary file: `x.md`\n", "must not point further")],
)
def test_broken_pointer_is_a_contract_error(tmp_path, pointed, reason):
    files = {"AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n"}
    if pointed is not None:
        files["glossary.md"] = pointed
    with pytest.raises(glossary.GlossaryError, match=reason):
        glossary.load_glossary(make_project(tmp_path, files))


def test_project_root_of_a_subdirectory_is_the_git_root(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD, "sub/x.txt": "x"})
    assert glossary.project_root(str(root / "sub")) == root.resolve()


def test_project_root_outside_git_is_the_directory_itself(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert glossary.project_root(str(plain)) == plain


MATCH_BODY = "\n".join([
    "- «реестр», «регистр» → **таблица**",
    "- «запись» → **строка**",
    "- «OOF» → **out-of-fold**",
    "- «k-fold» → **блочная проверка**",
    "- «TP» → **истинно положительный**",
    "- «K» → **ключ**",
    "- «dev set» → **отложенная выборка**",
    "- «кросс-валидация» → **перекрёстная проверка**",
    "- «валидация» → **проверка**",
    "- «scale_pos_weight» → **вес класса**",
    "- Исключение: «реестр моделей» — источник: model-registry.json",
])


def matcher():
    groups, exceptions, _ = parse(MATCH_BODY)
    return glossary.Glossary("test", groups, exceptions, section_of(MATCH_BODY), False)


def forms_in(text):
    return [f.form for f in glossary.scan_text(text, matcher())]


@pytest.mark.parametrize(
    "text",
    ["Это реестр данных", "Реестр данных", "в реестре", "реестром", "реестры", "о реестрах", "из реестра"],
)
def test_cyrillic_form_matches_case_and_endings(text):
    assert forms_in(text) == ["реестр"]


@pytest.mark.parametrize("text", ["записать данные", "записка автору", "табличный вид", "реестровый номер"])
def test_near_words_do_not_match(text):
    assert forms_in(text) == []


def test_form_with_final_vowel_keeps_its_case_endings():
    assert forms_in("новая запись, две записи, о записях, записью") == ["запись", "запись", "запись", "запись"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("слово OOF здесь", ["OOF"]),
        ("слово OOFS здесь", []),
        ("слово oof здесь", []),
        ("слово k-fold здесь", ["k-fold"]),
        ("слово k-folds здесь", []),
        ("слово K-fold здесь", []),
        ("слово TP здесь", ["TP"]),
        ("слово tp и TPU здесь", []),
        ("слово Q, K, V здесь", ["K"]),
        ("слово K=5 здесь", ["K"]),
        ("слово Ключ здесь", []),
        ("слово dev set здесь", ["dev set"]),
        ("слово dev sets и Dev Set здесь", []),
        ("слово dev   set здесь", ["dev set"]),
    ],
)
def test_latin_forms_are_literal_and_short_ones_whole_token(text, expected):
    assert forms_in(text) == expected


@pytest.mark.parametrize("text", ["слово реестр-сводка здесь", "слово DNS-реестр здесь", "слово реестр_x здесь"])
def test_a_hyphen_or_underscore_is_a_boundary_on_both_sides(text):
    assert forms_in(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "слово `реестр` здесь",
        "слово «реестр» здесь",
        "```\nреестр\n```\nслово здесь",
        "слово [реестр](https://example.org/a) здесь",
        "слово https://example.org/реестр здесь",
        "слово scale_pos_weight здесь",
        "слово registry.jsonl и docs/plan.md здесь",
        "слово camelCase и HTTPServer и reverse-WireGuard здесь",
        "слово H0 здесь",
        "English line with OOF in prose and nothing else",
    ],
)
def test_exempt_spans_are_not_read(text):
    assert forms_in(text) == []


def test_english_line_with_a_forbidden_latin_form_is_silent_and_the_same_form_on_a_cyrillic_line_fires():
    assert forms_in("This line has OOF in English prose.\nА здесь OOF в русской строке.") == ["OOF"]


def test_all_capital_abbreviation_stays_checkable_but_an_identifier_does_not():
    assert forms_in("слово OOF здесь и OOF_x там") == ["OOF"]


def test_exception_phrase_overlapping_a_form_drops_the_finding():
    assert forms_in("слово реестр моделей здесь") == []
    assert forms_in("слово реестр здесь и реестр моделей там") == ["реестр"]


def test_the_longest_form_wins_over_a_form_inside_it():
    assert forms_in("слово кросс-валидация здесь") == ["кросс-валидация"]
    assert forms_in("слово валидация здесь") == ["валидация"]


def test_findings_carry_line_number_form_and_canonical_in_text_order():
    found = glossary.scan_text("первая строка\nслово регистр и запись", matcher())
    assert found == [glossary.Finding(2, "регистр", "таблица"), glossary.Finding(2, "запись", "строка")]


def test_only_lines_limits_the_report():
    text = "слово реестр\nслово регистр"
    assert [f.line_no for f in glossary.scan_text(text, matcher(), only_lines={2})] == [2]


def test_changed_lines_marks_replaced_and_inserted_lines_only():
    assert glossary.changed_lines("a\nb\nc", "a\nB\nc\nd") == {2, 4}
    assert glossary.changed_lines(None, "a\nb") == {1, 2}


def run_mode(mode, payload, home, cwd=None):
    return subprocess.run(
        ["python3", str(HOOK), mode],
        input=payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


def memo(home, root, prompt="привет", **extra):
    return run_mode("memo", {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": str(root), **extra}, home)


def context_of(result, event):
    assert result.returncode == 0 and result.stderr == ""
    out = json.loads(result.stdout)
    assert "decision" not in out and out["hookSpecificOutput"]["hookEventName"] == event
    return out["hookSpecificOutput"]["additionalContext"]


def silent(result):
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def groups_section(count, prefix="термин"):
    return "".join(f"- «{prefix}{i}» → **канон{i}** — определение {i}\n" for i in range(count))


def test_memo_sends_the_whole_section_of_a_small_glossary(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD + "\n## Другое\n\nSTAYS-OUT\n"})
    context = context_of(memo(home, root), "UserPromptSubmit")
    assert "- «фича» → **признак** — столбец данных" in context and "STAYS-OUT" not in context
    assert str(root / "AGENTS.md") in context and "only the canonical terms" in context


def test_memo_resolves_a_subdirectory_to_the_project_root(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD, "sub/x.txt": "x"})
    assert "«фича»" in context_of(memo(home, root / "sub"), "UserPromptSubmit")


def test_memo_reads_claude_md_when_it_is_the_instruction_file(home, tmp_path):
    root = make_project(tmp_path, {"CLAUDE.md": GLOSSARY_MD})
    assert "«фича»" in context_of(memo(home, root), "UserPromptSubmit")


def test_memo_of_a_pointed_glossary_sends_only_the_touched_groups_in_file_order(home, tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "## Glossary\n\n" + groups_section(30),
    })
    context = context_of(memo(home, root, prompt="что значит канон7 и термин3?"), "UserPromptSubmit")
    sent = [line for line in context.splitlines() if line.startswith("- ")]
    assert sent == ["- «термин3» → **канон3** — определение 3", "- «термин7» → **канон7** — определение 7"]
    assert "2 of 30 groups" in context


def test_memo_of_a_pointed_glossary_with_nothing_touched_sends_the_pointer(home, tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "## Glossary\n\n" + groups_section(30),
    })
    context = context_of(memo(home, root, prompt="совсем другая тема"), "UserPromptSubmit")
    assert "30 groups" in context and "- «" not in context and "glossary.md" in context


@pytest.mark.parametrize(
    "section",
    [groups_section(201), "".join(f"- «т{i}» → **к{i}** — {'д' * 100}\n" for i in range(80))],
    ids=["201 lines", "over 8,000 characters"],
)
def test_memo_of_an_oversized_section_falls_back_to_the_pointer(home, tmp_path, section):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + section})
    context = context_of(memo(home, root, prompt="совсем другая тема"), "UserPromptSubmit")
    assert "groups," in context and "- «" not in context


def test_memo_caps_the_touched_groups_at_the_character_limit(home, tmp_path):
    section = "".join(f"- «слово» → **канон{i}** — {'д' * 200}\n" for i in range(60))
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `g.md`\n", "g.md": "## Glossary\n\n" + section})
    context = context_of(memo(home, root, prompt="слово"), "UserPromptSubmit")
    assert len(context) <= glossary.MEMO_MAX_CHARS + 400 and "groups touched" in context


@pytest.mark.parametrize("payload", ["", "not json", "[]", "42"])
def test_memo_malformed_input_is_silent(home, tmp_path, payload):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD})
    silent(run_mode("memo", payload, home, cwd=root))


def test_memo_without_a_glossary_is_silent_and_writes_no_journal(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nno glossary\n"})
    silent(memo(home, root))
    assert not (home / ".claude" / "hook-stats").exists()


def test_memo_without_git_or_instruction_file_is_silent(home, tmp_path):
    silent(memo(home, make_project(tmp_path, {}, git=False)))


def test_memo_with_a_broken_pointer_is_silent_and_journals_the_error(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(memo(home, root))
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"]) == ("glossary", "memo") and "unreadable" in record["error"]


def test_unknown_mode_is_a_usage_error(home):
    result = run_mode("bogus", {}, home)
    assert result.returncode == 2 and "usage" in result.stderr


FORMS_BODY = "- «кросс-валидация» → **перекрёстная проверка**\n- «фича» → **признак**\n- «лог» → **журнал**\n"
LONG_RU = "Это сообщение написано по-русски, чтобы строка считалась русской. "


def stop(home, root, message, **extra):
    return run_mode("stop", {"hook_event_name": "Stop", "last_assistant_message": message, "cwd": str(root), **extra}, home)


@pytest.fixture
def project(tmp_path):
    return make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + FORMS_BODY})


def test_stop_asks_for_one_line_per_forbidden_form_without_blocking(home, project):
    context = context_of(stop(home, project, LONG_RU + "Нужна кросс-валидация и ещё одна фича."), "Stop")
    assert "«кросс-валидация» → «перекрёстная проверка»" in context and "«фича» → «признак»" in context
    assert "Поправка к термину: «<form>» → «<canonical>»" in context and "ALREADY READ" in context


def test_stop_lists_each_distinct_form_once_in_order_of_first_occurrence(home, project):
    context = context_of(stop(home, project, LONG_RU + "Фича, потом лог, потом снова фича.\nИ ещё одна фича."), "Stop")
    listed = context.split("project glossary: ", 1)[1].split(".\n", 1)[0]
    assert listed == "«фича» → «признак», «лог» → «журнал»"


def test_stop_is_silent_when_the_message_uses_canonical_terms_only(home, project):
    silent(stop(home, project, LONG_RU + "Здесь только признак и журнал."))


def test_stop_is_silent_when_a_stop_hook_is_already_continuing(home, project):
    silent(stop(home, project, LONG_RU + "Фича.", stop_hook_active=True))


@pytest.mark.parametrize("payload", ["", "not json", "[]", "42"])
def test_stop_malformed_input_is_silent(home, project, payload):
    silent(run_mode("stop", payload, home, cwd=project))


def test_stop_without_a_glossary_is_silent_and_writes_no_journal(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nplain\n"})
    silent(stop(home, root, LONG_RU + "Фича."))
    assert not (home / ".claude" / "hook-stats").exists()


def test_stop_journals_the_findings_under_the_glossary_hook_name(home, project):
    stop(home, project, LONG_RU + "Фича и лог.")
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"], record["cwd"]) == ("glossary", "stop", str(project))
    assert record["findings"] == [["фича", "признак"], ["лог", "журнал"]]
    assert record["glossary"] == str(project / "AGENTS.md") and record["ts"].endswith("+00:00")


def test_stop_still_answers_when_the_journal_cannot_be_written(home, project):
    (home / ".claude").rmdir()
    (home / ".claude").write_text("a file where the journal directory should be")
    assert "«фича» → «признак»" in context_of(stop(home, project, LONG_RU + "Фича."), "Stop")


def test_stop_with_a_broken_pointer_is_silent(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(stop(home, root, LONG_RU + "Фича."))


def staged(home, root):
    return subprocess.run(
        ["python3", str(HOOK), "--staged"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


@pytest.fixture
def committed(tmp_path):
    """A project whose HEAD holds the glossary and a notes file with one old forbidden form."""
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + FORMS_BODY, "notes.md": "Старая фича в тексте.\nВторая строка.\n"})
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "-m", "init")
    return root


def test_staged_reports_only_the_new_forbidden_line_and_exits_1(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка.\nНовый лог добавлен.\n")
    sh(committed, "add", "notes.md")
    result = staged(home, committed)
    assert (result.returncode, result.stdout, result.stderr) == (1, "notes.md:3: «лог» → «журнал»\n", "")
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"], record["findings"]) == ("glossary", "staged", [["notes.md", 3, "лог", "журнал"]])


def test_staged_without_a_new_forbidden_form_passes_silently(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка изменена.\n")
    sh(committed, "add", "notes.md")
    result = staged(home, committed)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_staged_new_file_is_scanned_in_full(home, committed):
    (committed / "new.md").write_text("Строка раз.\nЛог тут.\n")
    sh(committed, "add", "new.md")
    assert staged(home, committed).stdout == "new.md:2: «лог» → «журнал»\n"


def test_staged_binary_file_is_skipped(home, committed):
    (committed / "blob.bin").write_bytes(b"\x00\xff\xfe" + "фича".encode())
    sh(committed, "add", "blob.bin")
    assert staged(home, committed).returncode == 0


def test_staged_reads_the_glossary_from_the_index_not_the_working_tree(home, committed):
    (committed / "AGENTS.md").write_text("## Glossary\n\n" + FORMS_BODY + "- «шина» → **канал**\n")  # edited, not staged
    (committed / "bus.md").write_text("Слово шина тут.\n")
    sh(committed, "add", "bus.md")
    assert staged(home, committed).returncode == 0


def test_staged_without_a_glossary_exits_0_silently(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nplain\n", "a.md": "Фича.\n"})
    sh(root, "add", "-A")
    result = staged(home, root)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert not (home / ".claude" / "hook-stats").exists()


def test_staged_contract_error_exits_2_with_the_reason(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n- «x» → без звёздочек\n"})
    sh(root, "add", "-A")
    result = staged(home, root)
    assert result.returncode == 2 and result.stdout.startswith("glossary: ") and "matches no glossary form" in result.stdout


def test_staged_broken_pointer_exits_2(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    sh(root, "add", "-A")
    assert staged(home, root).returncode == 2


def test_staged_checks_the_glossary_file_itself_for_foreign_forbidden_forms(home, tmp_path):
    body = "- «лог» → **журнал** — то же, что фича\n- «фича» → **признак**\n"
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + body})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "AGENTS.md:3: «фича» → «признак»\n"


def test_staged_follows_an_absolute_pointer_outside_the_repository(home, tmp_path):
    shared = tmp_path / "shared.md"
    shared.write_text("## Glossary\n\n" + FORMS_BODY)
    root = make_project(tmp_path, {"AGENTS.md": f"## Glossary\n\nGlossary file: `{shared}`\n", "a.md": "Новая фича.\n"})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "a.md:1: «фича» → «признак»\n"
