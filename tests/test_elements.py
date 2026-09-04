"""Наименования структурных элементов, принятые кафедрой вместо стандартных."""

from pathlib import Path

from nk.core.profile import Profile
from nk.core.registry import load_rules
from nk.parse.tex import parse

REPORT = """\
\\begin{document}
\\section*{РЕФЕРАТ}
Отчёт 45 с., 3 рис.
\\tableofcontents
\\section*{ВВЕДЕНИЕ}
Актуальность темы.
\\section{Выбор направления исследований}
Основная часть.
\\section*{ЗАКЛЮЧЕНИЕ}
Краткие выводы.
\\section*{СПИСОК ЛИТЕРАТУРЫ}
Записи.
\\end{document}
"""

MISSING = "G732-4-required-element-missing"
ORDER = "G732-4-elements-order"

ALIASES = {"СПИСОК ЛИТЕРАТУРЫ": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"}


def messages(tmp_path: Path, rule_id: str, profile: Profile, text: str = REPORT) -> list[str]:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    registry = load_rules()
    document = parse([path], profile=profile.resolve(registry.default_params())).document
    return [finding.message for finding in registry.get(rule_id)(document)]


def test_element_named_by_the_department_is_not_found_without_an_alias(tmp_path: Path) -> None:
    assert messages(tmp_path, MISSING, Profile()) == [
        "В отчёте нет структурного элемента «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ»."
    ]


def test_alias_makes_the_element_count(tmp_path: Path) -> None:
    assert messages(tmp_path, MISSING, Profile(element_aliases=ALIASES)) == []


def test_alias_also_gives_the_element_its_place_in_the_order(tmp_path: Path) -> None:
    assert messages(tmp_path, ORDER, Profile(element_aliases=ALIASES)) == []
