"""Встроенные профили: согласованность с реестром и поведение под ними."""

from importlib import resources
from pathlib import Path

import pytest

from nk.core.numbering import FIGURE
from nk.core.profile import BUILTIN_PACKAGE, PROFILE_SUFFIX, load_profile
from nk.core.registry import load_rules, select_rules, validate_profile
from nk.parse.tex import parse

MGTU = "mgtu-vkr"


def builtin_names() -> list[str]:
    return sorted(
        item.name.removesuffix(PROFILE_SUFFIX)
        for item in resources.files(BUILTIN_PACKAGE).iterdir()
        if item.name.endswith(PROFILE_SUFFIX)
    )


def findings(tmp_path: Path, text: str, profile_name: str, rule_id: str) -> list:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    registry = load_rules()
    profile = load_profile(profile_name).resolve(registry.default_params())
    return list(registry.get(rule_id)(parse([path], profile=profile).document))


def test_every_builtin_profile_is_listed() -> None:
    assert builtin_names() == ["base", MGTU]


@pytest.mark.parametrize("name", builtin_names())
def test_builtin_profile_matches_the_registry(name: str) -> None:
    """Переименованное правило обязано ронять встроенный профиль, а не молча его ломать."""
    registry = load_rules()
    profile = load_profile(name)

    validate_profile(profile, registry)
    assert select_rules(registry, profile=profile)


REPORT = """\
\\begin{document}
\\section*{АННОТАЦИЯ}
Отчёт 78 с.
\\newpage
\\section*{СОДЕРЖАНИЕ}
\\tableofcontents
\\newpage
\\section*{ВВЕДЕНИЕ}
Актуальность.
\\section{Обзор существующих решений}
Основная часть.
\\newpage
\\section*{ЗАКЛЮЧЕНИЕ}
Выводы.
\\newpage
\\section*{СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ}
Записи.
\\newpage
\\section*{ПРИЛОЖЕНИЕ 1}
\\begin{figure}\\includegraphics{a}\\end{figure}
\\end{document}
"""


def test_annotation_counts_as_the_abstract(tmp_path: Path) -> None:
    assert findings(tmp_path, REPORT, MGTU, "G732-4-required-element-missing") == []


def test_digits_are_valid_appendix_designations(tmp_path: Path) -> None:
    assert findings(tmp_path, REPORT, MGTU, "G732-6.17.4-appendix-letter") == []


def test_cyrillic_appendix_letter_is_a_finding_under_mgtu(tmp_path: Path) -> None:
    text = REPORT.replace("ПРИЛОЖЕНИЕ 1", "ПРИЛОЖЕНИЕ А")

    messages = [
        finding.message for finding in findings(tmp_path, text, MGTU, "G732-6.17.4-appendix-letter")
    ]

    assert messages == ["Приложение обозначено как «А»."]


def test_section_of_the_main_part_needs_no_page_break_under_mgtu(tmp_path: Path) -> None:
    assert findings(tmp_path, REPORT, MGTU, "G732-6.2.1-section-page-break") == []


def test_the_same_section_needs_one_under_base(tmp_path: Path) -> None:
    messages = [
        finding.lineno
        for finding in findings(tmp_path, REPORT, "base", "G732-6.2.1-section-page-break")
    ]

    assert messages == [10]


#: Нумерация в пределах раздела: при сквозной схеме счётчик в приложении
#: не сбрасывается, и обозначение приложения в номер не попадает.
APPENDIX_FIGURE = """\
\\counterwithin{figure}{section}
\\begin{document}
\\section*{ПРИЛОЖЕНИЕ %s}
\\begin{figure}\\includegraphics{a}\\end{figure}
\\end{document}
"""


def appendix_figure_number(tmp_path: Path, designation: str, profile_name: str) -> list[str]:
    path = tmp_path / "report.tex"
    path.write_text(APPENDIX_FIGURE % designation, encoding="utf-8")
    numbering = parse([path], profile=load_profile(profile_name)).document.numbering
    return [item.number for item in numbering.by_kind(FIGURE)]


def test_appendix_numbering_follows_the_profile_designations(tmp_path: Path) -> None:
    """Обозначение приложения из профиля попадает в номер рисунка."""
    assert appendix_figure_number(tmp_path, "1", MGTU) == ["1.1"]
    assert appendix_figure_number(tmp_path, "А", "base") == ["А.1"]
