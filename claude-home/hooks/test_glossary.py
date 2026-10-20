"""Tests for glossary.py — per-project synonym glossary: memo (UserPromptSubmit), stop (Stop), --staged (pre-commit).

A project keeps one `## Glossary` section in its AGENTS.md: one bullet per group of forbidden
synonyms with one canonical term. The memo delivers it before the answer, the Stop mode asks
for a one-line correction per forbidden form, the pre-commit mode refuses a commit that adds
one (bd python-ai-skills-du5). Isolation as in test_explanation_terms.py: a fake HOME and a
temporary git repository per test; fixtures are inline strings.
"""

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
