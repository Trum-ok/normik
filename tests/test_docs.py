from pathlib import Path

from nk.core import categories
from nk.core.registry import load_rules
from nk.report import examples, rules_docs

ROOT = Path(__file__).parent.parent
RULES_DIR = ROOT / "docs" / "rules"
FIXTURES = ROOT / "tests" / "fixtures"


def _pages() -> dict[str, str]:
    return rules_docs.render_pages(load_rules(), fixtures_root=FIXTURES)


def test_pages_are_up_to_date() -> None:
    stale = [
        name
        for name, text in _pages().items()
        if not (RULES_DIR / name).is_file()
        or (RULES_DIR / name).read_text(encoding="utf-8") != text
    ]
    assert stale == [], (
        f"страницы разошлись с реестром — перегенерируйте: uv run nk rules docs: {stale}"
    )


def test_no_pages_left_from_removed_rules() -> None:
    extra = sorted(path.name for path in RULES_DIR.glob("*.md") if path.name not in _pages())
    assert extra == [], f"страницы без правила в реестре: {extra}"


def test_every_rule_has_a_description() -> None:
    missing = [impl.id for impl in load_rules() if not impl.description]
    assert missing == [], f"правила без докстринга: {missing}"


def test_every_rule_page_shows_an_example() -> None:
    pages = _pages()
    missing = [impl.id for impl in load_rules() if "## Нарушение" not in pages[f"{impl.id}.md"]]
    assert missing == [], f"правила без примера из фикстур: {missing}"


def test_summary_lists_every_rule() -> None:
    summary = _pages()[rules_docs.SUMMARY_PAGE]
    missing = [impl.id for impl in load_rules() if f"({impl.id}.md)" not in summary]
    assert missing == [], f"правила без строки в оглавлении: {missing}"


def test_example_drops_test_markers() -> None:
    example = examples.load("figure-caption-dot", FIXTURES)
    assert example is not None
    assert examples.EXPECT_MARKER not in example.bad


def test_example_honours_doc_markers(tmp_path: Path) -> None:
    directory = tmp_path / "G732-x"
    directory.mkdir()
    (directory / examples.BAD_FILE).write_text(
        "\\section{Скрытое}\n% DOC-BEGIN\n\\caption{Схема.}\n% DOC-END\n\\section{Тоже}\n",
        encoding="utf-8",
    )
    (directory / examples.GOOD_FILE).write_text("\\caption{Схема}\n", encoding="utf-8")

    example = examples.load("G732-x", tmp_path)
    assert example is not None
    assert example.bad == "\\caption{Схема.}"


def test_example_is_absent_without_fixtures(tmp_path: Path) -> None:
    assert examples.load("G732-нет-такого", tmp_path) is None


def test_summary_groups_rules_by_category() -> None:
    summary = _pages()[rules_docs.SUMMARY_PAGE]

    for category in categories.CATEGORIES:
        assert f"* {category.title}" in summary, category.name


def test_every_rule_belongs_to_a_declared_category() -> None:
    """Правило вне категории выпало бы из оглавления молча."""
    misplaced = [impl.id for impl in load_rules() if impl.category not in categories.BY_NAME]

    assert misplaced == []
