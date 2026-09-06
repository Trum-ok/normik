"""Настройка состава и наименований структурных элементов профилем."""

from dataclasses import replace
from pathlib import Path

from nk.core.elements import DEFAULT_ELEMENTS, Elements
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


def with_aliases() -> Elements:
    return replace(DEFAULT_ELEMENTS, aliases=ALIASES)


def findings(tmp_path: Path, rule_id: str, profile: Profile, text: str = REPORT) -> list:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    registry = load_rules()
    document = parse([path], profile=profile.resolve(registry.default_params())).document
    return list(registry.get(rule_id)(document))


def messages(tmp_path: Path, rule_id: str, profile: Profile, text: str = REPORT) -> list[str]:
    return [finding.message for finding in findings(tmp_path, rule_id, profile, text)]


def test_element_named_by_the_department_is_not_found_without_an_alias(tmp_path: Path) -> None:
    assert messages(tmp_path, MISSING, Profile()) == [
        "В отчёте нет структурного элемента «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ»."
    ]


def test_alias_makes_the_element_count(tmp_path: Path) -> None:
    assert messages(tmp_path, MISSING, Profile(elements=with_aliases())) == []


def test_alias_also_gives_the_element_its_place_in_the_order(tmp_path: Path) -> None:
    assert messages(tmp_path, ORDER, Profile(elements=with_aliases())) == []


def test_excluded_drops_an_element_from_the_required_set(tmp_path: Path) -> None:
    text = REPORT.replace("\\section*{РЕФЕРАТ}\nОтчёт 45 с., 3 рис.\n", "")
    profile = Profile(params={MISSING: {"excluded": ["Реферат"]}}, elements=with_aliases())

    assert messages(tmp_path, MISSING, profile, text) == []


def test_required_replaces_the_set_entirely(tmp_path: Path) -> None:
    profile = Profile(params={MISSING: {"required": ["ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"]}})

    assert messages(tmp_path, MISSING, profile) == [
        "В отчёте нет структурного элемента «ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ»."
    ]


def test_unknown_name_in_required_is_reported_not_ignored(tmp_path: Path) -> None:
    """Опечатка в профиле обязана быть заметной, а не выключать проверку молча."""
    profile = Profile(params={MISSING: {"required": ["ЗАКЛЮЧЕНЕИ"]}})

    assert messages(tmp_path, MISSING, profile) == [
        "В отчёте нет структурного элемента «ЗАКЛЮЧЕНЕИ»."
    ]


def test_own_composition_leaves_the_report_without_known_elements(tmp_path: Path) -> None:
    """Источник требований со своим составом не видит элементов чужого состава."""
    elements = Elements(order={"ПРЕДИСЛОВИЕ": 1}, roles={})
    profile = Profile(params={MISSING: {"required": ["ПРЕДИСЛОВИЕ"]}}, elements=elements)

    assert messages(tmp_path, MISSING, profile) == [
        "В отчёте нет структурного элемента «ПРЕДИСЛОВИЕ»."
    ]


def test_own_order_changes_which_element_is_out_of_place(tmp_path: Path) -> None:
    """При обратном порядке не на месте оказывается заключение, а не введение."""
    elements = Elements(
        order={"РЕФЕРАТ": 1, "ЗАКЛЮЧЕНИЕ": 2, "ВВЕДЕНИЕ": 3, "СПИСОК ЛИТЕРАТУРЫ": 4},
        roles={},
    )

    assert messages(tmp_path, ORDER, Profile(elements=elements)) == [
        "Элемент «ЗАКЛЮЧЕНИЕ» стоит после «ВВЕДЕНИЕ»."
    ]


def test_requirement_names_the_order_of_this_profile(tmp_path: Path) -> None:
    """Находка называет порядок, по которому проверяется отчёт, а не порядок по умолчанию."""
    elements = Elements(order={"ЗАКЛЮЧЕНИЕ": 1, "ВВЕДЕНИЕ": 2}, roles={})

    found = findings(tmp_path, ORDER, Profile(elements=elements))

    assert [finding.requirement for finding in found] == [
        "Структурные элементы следуют в порядке: заключение, введение."
    ]
