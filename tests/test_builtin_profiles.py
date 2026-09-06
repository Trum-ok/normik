"""Встроенные профили: согласованность с реестром и поведение под ними."""

from importlib import resources
from pathlib import Path

import pytest

from nk.core.numbering import FIGURE
from nk.core.profile import BUILTIN_PACKAGE, PROFILE_SUFFIX, load_profile
from nk.core.registry import load_rules, select_rules, validate_profile
from nk.parse.tex import parse

BMSTU = "bmstu-vkr"
ESKD = "gost-r-2.105"


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
    assert builtin_names() == ["base", BMSTU, ESKD]


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
    assert findings(tmp_path, REPORT, BMSTU, "required-element-missing") == []


def test_digits_are_valid_appendix_designations(tmp_path: Path) -> None:
    assert findings(tmp_path, REPORT, BMSTU, "appendix-letter") == []


def test_cyrillic_appendix_letter_is_a_finding_under_bmstu(tmp_path: Path) -> None:
    text = REPORT.replace("ПРИЛОЖЕНИЕ 1", "ПРИЛОЖЕНИЕ А")

    messages = [finding.message for finding in findings(tmp_path, text, BMSTU, "appendix-letter")]

    assert messages == ["Приложение обозначено как «А»."]


def test_section_of_the_main_part_needs_no_page_break_under_bmstu(tmp_path: Path) -> None:
    assert findings(tmp_path, REPORT, BMSTU, "section-page-break") == []


def test_the_same_section_needs_one_under_base(tmp_path: Path) -> None:
    messages = [
        finding.lineno for finding in findings(tmp_path, REPORT, "base", "section-page-break")
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
    assert appendix_figure_number(tmp_path, "1", BMSTU) == ["1.1"]
    assert appendix_figure_number(tmp_path, "А", "base") == ["А.1"]


def test_finding_cites_the_regulation_where_it_diverges(tmp_path: Path) -> None:
    """Там, где положение расходится со стандартом, находка ссылается на положение."""
    text = REPORT.replace("ПРИЛОЖЕНИЕ 1", "ПРИЛОЖЕНИЕ 2")

    found = findings(tmp_path, text, BMSTU, "appendix-sequence")

    assert [(f.clause, f.source) for f in found] == [
        ("10.11", "Положение МГТУ им. Н.Э. Баумана № 01-01-ПЛ-016 01-2024")
    ]


def test_the_same_rule_cites_the_standard_under_base(tmp_path: Path) -> None:
    text = REPORT.replace("ПРИЛОЖЕНИЕ 1", "ПРИЛОЖЕНИЕ Б")

    found = findings(tmp_path, text, "base", "appendix-sequence")

    assert [(f.clause, f.source) for f in found] == [("6.17.4", "ГОСТ 7.32-2017")]


def test_rules_outside_the_standard_do_not_run(tmp_path: Path) -> None:
    """Реферата в ГОСТ Р 2.105 нет, и правила о нём под ним не запускаются."""
    registry = load_rules()
    chosen = {impl.id for impl in select_rules(registry, profile=load_profile(ESKD))}

    assert "keywords-count" not in chosen
    assert "abstract-volume-info" not in chosen
    assert "structural-heading-case" not in chosen
    assert "table-caption-position" in chosen


def test_the_same_rules_run_under_the_report_standard() -> None:
    registry = load_rules()
    chosen = {impl.id for impl in select_rules(registry, profile=load_profile("base"))}

    assert {"keywords-count", "abstract-volume-info", "structural-heading-case"} <= chosen


def test_shared_rule_cites_the_active_standard(tmp_path: Path) -> None:
    """Одно правило, два стандарта, разные пункты."""
    source = (
        "\\begin{table}\n"
        "\\begin{tabular}{ll}a&b\\\\c&d\\end{tabular}\n"
        "\\caption{Показатели}\n"
        "\\end{table}\n"
    )

    for profile_name, expected in (
        ("base", ("6.6.3", "ГОСТ 7.32-2017")),
        (ESKD, ("6.8.1", "ГОСТ Р 2.105-2019")),
    ):
        found = findings(tmp_path, source, profile_name, "table-caption-position")
        assert [(f.clause, f.source) for f in found] == [expected], profile_name


FORMULAS = """\
Плотность и объём вычисляют по формулам

\\begin{equation}
    \\rho = m / V
\\end{equation}
\\begin{equation}
    V = a b c
\\end{equation}
"""


def test_regulation_enables_a_rule_from_another_standard(tmp_path: Path) -> None:
    """Положение требует запятой между формулами, а ГОСТ 7.32 — нет."""
    found = findings(tmp_path, FORMULAS, BMSTU, "formula-sequence-comma")

    assert [(f.clause, f.source) for f in found] == [
        ("10.7", "Положение МГТУ им. Н.Э. Баумана № 01-01-ПЛ-016 01-2024")
    ]


def test_the_same_rule_stays_off_under_the_report_standard(tmp_path: Path) -> None:
    registry = load_rules()
    chosen = {impl.id for impl in select_rules(registry, profile=load_profile("base"))}

    assert "formula-sequence-comma" not in chosen


LONGTABLE = """\
\\begin{longtable}{ll}
  \\caption{Показатели} \\\\
  Показатель & Значение \\\\
  \\endhead
  Масса, кг & 12,5 \\\\
\\end{longtable}
"""


def test_continuation_is_required_by_the_report_standard(tmp_path: Path) -> None:
    found = findings(tmp_path, LONGTABLE, "base", "table-continuation")

    assert [(f.clause, f.source) for f in found] == [("6.6.3", "ГОСТ 7.32-2017")]


def test_continuation_is_not_required_by_the_eskd_standard(tmp_path: Path) -> None:
    """ГОСТ Р 2.105 надпись при машинной подготовке документа не требует."""
    registry = load_rules()
    chosen = {impl.id for impl in select_rules(registry, profile=load_profile(ESKD))}

    assert "table-continuation" not in chosen


def test_regulation_enables_a_rule_outside_every_standard(tmp_path: Path) -> None:
    """Оборот ссылки на рисунок задаёт положение, а не стандарт."""
    registry = load_rules()
    under_base = {impl.id for impl in select_rules(registry, profile=load_profile("base"))}
    under_bmstu = {impl.id for impl in select_rules(registry, profile=load_profile(BMSTU))}

    assert "figure-reference-form" not in under_base
    assert "figure-reference-form" in under_bmstu

    text = "Схема приведена на рисунке 2.\n"
    found = findings(tmp_path, text, BMSTU, "figure-reference-form")
    assert [(f.clause, f.source) for f in found] == [
        ("10.5", "Положение МГТУ им. Н.Э. Баумана № 01-01-ПЛ-016 01-2024")
    ]
