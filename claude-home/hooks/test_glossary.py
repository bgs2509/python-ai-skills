"""Tests for glossary.py — per-project synonym glossary: memo (UserPromptSubmit), stop (Stop), --staged (pre-commit).

A project keeps one `## Glossary` section in its AGENTS.md: one bullet per group of forbidden
synonyms with one canonical term. The memo delivers it before the answer, the Stop mode asks
for a one-line correction per forbidden form, the pre-commit mode refuses a commit that adds
one (bd python-ai-skills-du5). Isolation as in test_explanation_terms.py: a fake HOME and a
temporary git repository per test; fixtures are inline strings.
"""

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
