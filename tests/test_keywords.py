"""Правки перечня ключевых слов: что автоисправление трогает, а что оставляет."""

from pathlib import Path

from nk.core.fixer import plan
from nk.core.registry import load_rules
from nk.parse.tex import parse

DOT = "G732-6.12.2-keywords-final-dot"
UPPERCASE = "G732-6.12.2-keywords-uppercase"

HEADING = "\\section*{РЕФЕРАТ}\n\n"


def fixed(tmp_path: Path, rule_id: str, text: str) -> str | None:
    """Содержимое файла после правок правила либо ``None``, если правок нет."""
    path = tmp_path / "report.tex"
    path.write_text(HEADING + text, encoding="utf-8")
    document = parse([path]).document
    findings = list(load_rules().get(rule_id)(document))
    assert len(findings) == 1
    edits = plan(findings).edits
    return edits[0].text if edits else None


def test_comment_after_the_list_survives_the_fix(tmp_path: Path) -> None:
    text = fixed(tmp_path, UPPERCASE, "КЛЮЧЕВЫЕ СЛОВА: линтер, гост % пояснение\n")
    assert text is not None
    assert "КЛЮЧЕВЫЕ СЛОВА: ЛИНТЕР, ГОСТ % пояснение" in text


def test_markup_in_the_list_blocks_the_case_fix(tmp_path: Path) -> None:
    assert fixed(tmp_path, UPPERCASE, "КЛЮЧЕВЫЕ СЛОВА: \\textbf{линтер}, гост\n") is None


def test_list_broken_across_lines_blocks_the_case_fix(tmp_path: Path) -> None:
    assert fixed(tmp_path, UPPERCASE, "КЛЮЧЕВЫЕ СЛОВА: линтер,\nгост\n") is None


def test_final_dot_is_removed_on_the_last_line_of_the_list(tmp_path: Path) -> None:
    text = fixed(tmp_path, DOT, "КЛЮЧЕВЫЕ СЛОВА: ЛИНТЕР,\nГОСТ.\n")
    assert text is not None
    assert text.endswith("КЛЮЧЕВЫЕ СЛОВА: ЛИНТЕР,\nГОСТ\n")


def test_final_dot_inside_a_command_is_removed_without_the_brace(tmp_path: Path) -> None:
    text = fixed(tmp_path, DOT, "\\keywords{КЛЮЧЕВЫЕ СЛОВА: ЛИНТЕР, ГОСТ.}\n")
    assert text is not None
    assert "\\keywords{КЛЮЧЕВЫЕ СЛОВА: ЛИНТЕР, ГОСТ}" in text
