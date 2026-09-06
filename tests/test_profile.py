from dataclasses import replace
from pathlib import Path

import pytest

from nk.core import standards
from nk.core.elements import DEFAULT_ELEMENTS, TERMS_ROLE
from nk.core.finding import Severity
from nk.core.profile import Profile, ProfileError, discover, load_profile


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_empty_profile_changes_nothing() -> None:
    profile = Profile()
    assert not profile.is_disabled("figure-caption-dot")
    assert profile.severity_for("figure-caption-dot", Severity.ERROR) is Severity.ERROR
    assert profile.params_for("figure-caption-dot") == {}


def test_disable_and_severity_override() -> None:
    profile = Profile(
        name="Кафедра N",
        disabled=frozenset({"G732-4-required-elements"}),
        severities={"heading-hyphenation": Severity.WARNING},
    )
    assert profile.is_disabled("G732-4-required-elements")
    assert profile.severity_for("heading-hyphenation", Severity.ERROR) is Severity.WARNING


def test_resolve_merges_defaults_with_overrides() -> None:
    profile = Profile(params={"keywords-count": {"keywords_max": 20}})
    resolved = profile.resolve({"keywords-count": {"keywords_min": 5, "keywords_max": 15}})
    assert resolved.params_for("keywords-count") == {
        "keywords_min": 5,
        "keywords_max": 20,
    }


def test_resolve_keeps_defaults_for_untouched_rules() -> None:
    resolved = Profile().resolve({"G732-x": {"limit": 3}})
    assert resolved.params_for("G732-x") == {"limit": 3}


def test_mentioned_rules_covers_every_section() -> None:
    profile = Profile(
        disabled=frozenset({"G732-a"}),
        severities={"G732-b": Severity.INFO},
        params={"G732-c": {"limit": 1}},
    )
    assert profile.mentioned_rules() == frozenset({"G732-a", "G732-b", "G732-c"})


def test_builtin_base_is_the_default() -> None:
    profile = load_profile()
    assert profile.name == "base"
    assert profile.disabled == frozenset()


def test_load_from_file(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "кафедра.toml",
        """
        name = "Кафедра N"
        disable = ["G732-a"]

        [rules."G732-b"]
        severity = "warning"

        [rules."G732-c".params]
        keywords_min = 7
        """,
    )

    profile = load_profile(path)

    assert profile.name == "Кафедра N"
    assert profile.disabled == frozenset({"G732-a"})
    assert profile.severity_for("G732-b", Severity.ERROR) is Severity.WARNING
    assert profile.params_for("G732-c") == {"keywords_min": 7}


def test_extends_builtin_base(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "кафедра.toml",
        'name = "Кафедра N"\nextends = "base"\ndisable = ["G732-a"]\n',
    )

    profile = load_profile(path)
    assert profile.name == "Кафедра N"
    assert profile.disabled == frozenset({"G732-a"})


def test_extends_a_neighbouring_file(tmp_path: Path) -> None:
    write(
        tmp_path,
        "родитель.toml",
        'name = "Родитель"\ndisable = ["G732-a"]\n\n[rules."G732-b".params]\nlimit = 1\nstep = 2\n',
    )
    child = write(
        tmp_path,
        "ребёнок.toml",
        'name = "Ребёнок"\nextends = "родитель"\ndisable = ["G732-z"]\n\n'
        '[rules."G732-b"]\nseverity = "info"\n\n[rules."G732-b".params]\nlimit = 9\n',
    )

    profile = load_profile(child)

    assert profile.name == "Ребёнок"
    assert profile.disabled == frozenset({"G732-a", "G732-z"})
    assert profile.severity_for("G732-b", Severity.ERROR) is Severity.INFO
    assert profile.params_for("G732-b") == {"limit": 9, "step": 2}


def test_extends_forms_a_chain(tmp_path: Path) -> None:
    """Кафедра наследуется от вуза, вуз — от стандарта."""
    write(tmp_path, "дед.toml", 'name = "Дед"\ndisable = ["heading-dot"]\n')
    write(tmp_path, "отец.toml", 'name = "Отец"\nextends = "дед"\ndisable = ["heading-empty"]\n')
    child = write(tmp_path, "сын.toml", 'name = "Сын"\nextends = "отец"\n')

    profile = load_profile(child)

    assert profile.name == "Сын"
    assert profile.disabled == frozenset({"heading-dot", "heading-empty"})


def test_the_nearest_profile_wins_along_the_chain(tmp_path: Path) -> None:
    write(tmp_path, "дед.toml", '[rules."heading-dot"]\nseverity = "info"\n')
    write(
        tmp_path,
        "отец.toml",
        'extends = "дед"\n\n[rules."heading-dot"]\nseverity = "warning"\n',
    )
    child = write(tmp_path, "сын.toml", 'name = "Сын"\nextends = "отец"\n')

    profile = load_profile(child)

    assert profile.severity_for("heading-dot", Severity.ERROR) is Severity.WARNING


def test_a_builtin_profile_can_be_extended(tmp_path: Path) -> None:
    """Готовый профиль вуза сам наследуется от base, и это больше не мешает."""
    path = write(tmp_path, "кафедра.toml", 'name = "Кафедра"\nextends = "bmstu-vkr"\n')

    profile = load_profile(path)

    assert profile.name == "Кафедра"
    assert profile.source_title.startswith("Положение МГТУ")
    assert profile.appendix_letters == "123456789"


def test_a_cycle_is_rejected(tmp_path: Path) -> None:
    write(tmp_path, "первый.toml", 'extends = "второй"\n')
    path = write(tmp_path, "второй.toml", 'extends = "первый"\n')

    with pytest.raises(ProfileError, match="по кругу"):
        load_profile(path)


def test_self_extends_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "сам.toml", 'name = "Сам"\nextends = "сам"\n')

    with pytest.raises(ProfileError, match="по кругу"):
        load_profile(path)


def test_unknown_profile_name() -> None:
    with pytest.raises(ProfileError, match="не найден"):
        load_profile("нет-такого-профиля")


def test_broken_toml(tmp_path: Path) -> None:
    path = write(tmp_path, "битый.toml", "name = \n")

    with pytest.raises(ProfileError):
        load_profile(path)


def test_unknown_top_level_key(tmp_path: Path) -> None:
    path = write(tmp_path, "опечатка.toml", 'name = "X"\ndisabled = ["G732-a"]\n')

    with pytest.raises(ProfileError, match="неизвестные ключи"):
        load_profile(path)


def test_unknown_rule_key(tmp_path: Path) -> None:
    path = write(tmp_path, "опечатка.toml", '[rules."G732-a"]\nlevel = "warning"\n')

    with pytest.raises(ProfileError, match="неизвестные ключи"):
        load_profile(path)


def test_invalid_severity(tmp_path: Path) -> None:
    path = write(tmp_path, "уровень.toml", '[rules."G732-a"]\nseverity = "критично"\n')

    with pytest.raises(ProfileError, match="недопустимый уровень"):
        load_profile(path)


def test_enable_is_read_from_toml(tmp_path: Path) -> None:
    path = write(tmp_path, "кафедра.toml", 'enable = ["preposition-nbsp"]\n')

    profile = load_profile(path)

    assert profile.is_enabled("preposition-nbsp")
    assert "preposition-nbsp" in profile.mentioned_rules()


def test_enable_accumulates_through_extends(tmp_path: Path) -> None:
    write(tmp_path, "родитель.toml", 'enable = ["NK-STYLE-a"]\n')
    child = write(tmp_path, "ребёнок.toml", 'extends = "родитель"\nenable = ["NK-STYLE-b"]\n')

    assert load_profile(child).enabled == frozenset({"NK-STYLE-a", "NK-STYLE-b"})


def test_element_aliases_are_normalized(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "кафедра.toml",
        '[elements.aliases]\n"Список литературы." = "список использованных источников"\n',
    )

    profile = load_profile(path)

    assert profile.elements.aliases == {"СПИСОК ЛИТЕРАТУРЫ": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"}


def test_alias_to_an_unknown_element_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "кафедра.toml", '[elements.aliases]\n"ЛИТЕРАТУРА" = "БИБЛИОГРАФИЯ"\n')

    with pytest.raises(ProfileError, match="не структурный элемент"):
        load_profile(path)


def test_unknown_key_in_elements_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "кафедра.toml", "[elements]\nextra = []\n")

    with pytest.raises(ProfileError, match="неизвестные ключи"):
        load_profile(path)


def test_element_aliases_are_inherited_and_extended(tmp_path: Path) -> None:
    write(
        tmp_path,
        "основа.toml",
        '[elements.aliases]\n"СПИСОК ЛИТЕРАТУРЫ" = "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"\n',
    )
    path = write(
        tmp_path,
        "кафедра.toml",
        'extends = "основа.toml"\n[elements.aliases]\n"ОБОЗНАЧЕНИЯ" = "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ"\n',
    )

    profile = load_profile(path)

    assert profile.elements.aliases == {
        "СПИСОК ЛИТЕРАТУРЫ": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        "ОБОЗНАЧЕНИЯ": "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
    }


def test_order_replaces_the_composition_of_elements(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "источник.toml",
        '[elements.order]\n"ПРЕДИСЛОВИЕ" = 1\n"СОДЕРЖАНИЕ" = 2\n',
    )

    profile = load_profile(path)

    assert profile.elements.names == frozenset({"ПРЕДИСЛОВИЕ", "СОДЕРЖАНИЕ"})
    assert profile.elements.ordered() == (("ПРЕДИСЛОВИЕ",), ("СОДЕРЖАНИЕ",))


def test_elements_sharing_a_rank_share_a_place(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "источник.toml",
        '[elements.order]\n"ТЕРМИНЫ" = 1\n"ОПРЕДЕЛЕНИЯ" = 1\n"ВВЕДЕНИЕ" = 2\n',
    )

    assert load_profile(path).elements.ordered() == (("ОПРЕДЕЛЕНИЯ", "ТЕРМИНЫ"), ("ВВЕДЕНИЕ",))


def test_own_order_makes_the_old_composition_unknown(tmp_path: Path) -> None:
    """Иначе от источника, от которого уходили, оставались бы его элементы."""
    path = write(tmp_path, "источник.toml", '[elements.order]\n"ПРЕДИСЛОВИЕ" = 1\n')

    assert "РЕФЕРАТ" not in load_profile(path).elements.names


def test_roles_are_read_from_the_profile(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "источник.toml",
        '[elements.order]\n"Обозначения и термины" = 1\n\n'
        '[elements.roles]\nterms = ["ОБОЗНАЧЕНИЯ И ТЕРМИНЫ"]\n',
    )

    assert load_profile(path).elements.role(TERMS_ROLE) == frozenset({"ОБОЗНАЧЕНИЯ И ТЕРМИНЫ"})


def test_unknown_role_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", '[elements.roles]\n"преамбула" = ["РЕФЕРАТ"]\n')

    with pytest.raises(ProfileError, match="неизвестные роли"):
        load_profile(path)


def test_role_pointing_outside_the_composition_is_rejected(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "источник.toml",
        '[elements.order]\n"ВВЕДЕНИЕ" = 1\n\n[elements.roles]\nabstract = ["РЕФЕРАТ"]\n',
    )

    with pytest.raises(ProfileError, match="вне состава"):
        load_profile(path)


def test_rank_must_be_a_whole_number(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", '[elements.order]\n"ВВЕДЕНИЕ" = "первое"\n')

    with pytest.raises(ProfileError, match="должен быть целым"):
        load_profile(path)


def test_empty_order_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", "[elements.order]\n")

    with pytest.raises(ProfileError, match="состав элементов задавать нечем"):
        load_profile(path)


def test_own_order_keeps_inherited_aliases(tmp_path: Path) -> None:
    write(
        tmp_path,
        "основа.toml",
        '[elements.aliases]\n"ЛИТЕРАТУРА" = "СОДЕРЖАНИЕ"\n',
    )
    path = write(
        tmp_path,
        "кафедра.toml",
        'extends = "основа.toml"\n[elements.order]\n"СОДЕРЖАНИЕ" = 1\n',
    )

    profile = load_profile(path)

    assert profile.elements.names == frozenset({"СОДЕРЖАНИЕ"})
    assert profile.elements.aliases == {"ЛИТЕРАТУРА": "СОДЕРЖАНИЕ"}


def test_inherited_alias_outside_the_new_composition_is_rejected(tmp_path: Path) -> None:
    write(tmp_path, "основа.toml", '[elements.aliases]\n"ЛИТЕРАТУРА" = "РЕФЕРАТ"\n')
    path = write(
        tmp_path,
        "кафедра.toml",
        'extends = "основа.toml"\n[elements.order]\n"СОДЕРЖАНИЕ" = 1\n',
    )

    with pytest.raises(ProfileError, match="не структурный элемент"):
        load_profile(path)


def test_resolve_keeps_the_element_dictionary() -> None:
    elements = replace(
        DEFAULT_ELEMENTS, aliases={"СПИСОК ЛИТЕРАТУРЫ": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"}
    )
    profile = Profile(elements=elements)

    assert profile.resolve({}).elements == elements


def test_appendix_letters_are_read_from_the_profile(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", '[appendix]\nletters = "123456789"\n')

    assert load_profile(path).appendix_letters == "123456789"


def test_appendix_letters_default_to_cyrillic() -> None:
    assert Profile().appendix_letters.startswith("АБВ")


def test_repeated_appendix_letter_is_rejected(tmp_path: Path) -> None:
    """По обозначению определяется место приложения, а у повторённого мест два."""
    path = write(tmp_path, "источник.toml", '[appendix]\nletters = "ABA"\n')

    with pytest.raises(ProfileError, match="знаки повторяются"):
        load_profile(path)


def test_empty_appendix_letters_are_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", '[appendix]\nletters = "  "\n')

    with pytest.raises(ProfileError, match="обозначать приложения нечем"):
        load_profile(path)


def test_unknown_key_in_appendix_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", "[appendix]\nextra = 1\n")

    with pytest.raises(ProfileError, match="неизвестные ключи"):
        load_profile(path)


def test_appendix_letters_are_inherited(tmp_path: Path) -> None:
    write(tmp_path, "основа.toml", '[appendix]\nletters = "123456789"\n')
    path = write(tmp_path, "кафедра.toml", 'extends = "основа.toml"\n')

    assert load_profile(path).appendix_letters == "123456789"


def test_resolve_keeps_appendix_letters() -> None:
    assert Profile(appendix_letters="XYZ").resolve({}).appendix_letters == "XYZ"


def test_standard_is_read_from_the_profile(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", 'standard = "GR2105"\n')

    assert load_profile(path).standard is standards.GR2105


def test_standard_defaults_to_the_report_standard() -> None:
    assert Profile().standard is standards.DEFAULT


def test_unknown_standard_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "источник.toml", 'standard = "G0000"\n')

    with pytest.raises(ProfileError, match="неизвестный стандарт"):
        load_profile(path)


def test_clause_without_a_named_source_is_rejected(tmp_path: Path) -> None:
    """Пункт без источника непонятно чей."""
    path = write(tmp_path, "источник.toml", '[rules."heading-dot"]\nclause = "9.3"\n')

    with pytest.raises(ProfileError, match="источник не назван"):
        load_profile(path)


def test_own_clause_wins_over_the_standard(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "источник.toml",
        '[source]\ntitle = "Положение"\n\n[rules."heading-dot"]\nclause = "9.3"\n',
    )

    profile = load_profile(path)

    assert profile.requirement("heading-dot", {"G732": "6.2.3"}) == ("9.3", "Положение")


def test_clause_of_the_active_standard_is_used_by_default() -> None:
    clauses = {"G732": "6.5.7", "GR2105": "6.9.4"}

    assert Profile().requirement("caption-dot", clauses) == ("6.5.7", "ГОСТ 7.32-2017")
    assert Profile(standard=standards.GR2105).requirement("caption-dot", clauses) == (
        "6.9.4",
        "ГОСТ Р 2.105-2019",
    )


def test_rule_outside_the_active_standard_has_neither_clause_nor_source() -> None:
    """Иначе типографика ссылалась бы на стандарт, который её не регулирует."""
    profile = Profile(standard=standards.GR2105)

    assert profile.requirement("keywords-count", {"G732": "5.3.2.1"}) == ("", "")
    assert profile.requirement("unit-nbsp", {}) == ("", "")


def test_standard_and_source_are_inherited(tmp_path: Path) -> None:
    write(tmp_path, "основа.toml", 'standard = "GR2105"\n\n[source]\ntitle = "Положение"\n')
    path = write(tmp_path, "кафедра.toml", 'extends = "основа.toml"\n')

    profile = load_profile(path)

    assert profile.standard is standards.GR2105
    assert profile.source_title == "Положение"


def test_own_clauses_are_checked_against_the_registry(tmp_path: Path) -> None:
    """Опечатка в идентификаторе не должна молча терять пункт."""
    path = write(
        tmp_path,
        "источник.toml",
        '[source]\ntitle = "Положение"\n\n[rules."опечатка"]\nclause = "9.3"\n',
    )

    assert "опечатка" in load_profile(path).mentioned_rules()


def test_discover_finds_nk_toml(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Кафедра N"\n')
    (tmp_path / "chapters").mkdir()

    assert discover([tmp_path / "chapters"]) == tmp_path / "nk.toml"


def test_discover_prefers_nk_toml_to_pyproject(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Из nk.toml"\n')
    write(tmp_path, "pyproject.toml", '[tool.nk]\nname = "Из pyproject"\n')

    assert discover([tmp_path]) == tmp_path / "nk.toml"


def test_discover_skips_pyproject_without_section(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Кафедра N"\n')
    nested = tmp_path / "работа"
    nested.mkdir()
    write(nested, "pyproject.toml", '[project]\nname = "чужой"\n')

    assert discover([nested]) == tmp_path / "nk.toml"


def test_discover_starts_from_the_common_root(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Общий"\n')
    for name in ("главы", "приложения"):
        (tmp_path / name).mkdir()
    write(tmp_path / "главы", "nk.toml", 'name = "Только главы"\n')

    found = discover([tmp_path / "главы", tmp_path / "приложения"])

    assert found == tmp_path / "nk.toml"


def test_discover_starts_from_the_parent_of_a_file(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Кафедра N"\n')
    report = write(tmp_path, "report.tex", "")

    assert discover([report]) == tmp_path / "nk.toml"


def test_load_reads_the_pyproject_section(tmp_path: Path) -> None:
    write(
        tmp_path,
        "pyproject.toml",
        '[project]\nname = "diploma"\n\n[tool.nk]\nname = "Кафедра N"\n'
        'disable = ["G732-a"]\n\n[tool.nk.rules."G732-b"]\nseverity = "warning"\n',
    )

    profile = load_profile(search_from=[tmp_path])

    assert profile.name == "Кафедра N"
    assert profile.disabled == frozenset({"G732-a"})
    assert profile.severity_for("G732-b", Severity.ERROR) is Severity.WARNING
    assert profile.source == tmp_path / "pyproject.toml"


def test_pyproject_without_section_is_rejected_when_given_explicitly(tmp_path: Path) -> None:
    path = write(tmp_path, "pyproject.toml", '[project]\nname = "diploma"\n')

    with pytest.raises(ProfileError, match=r"нет секции \[tool.nk\]"):
        load_profile(path)


def test_pyproject_section_extends_a_neighbouring_file(tmp_path: Path) -> None:
    write(tmp_path, "родитель.toml", 'name = "Родитель"\ndisable = ["G732-a"]\n')
    write(tmp_path, "pyproject.toml", '[tool.nk]\nextends = "родитель"\ndisable = ["G732-z"]\n')

    profile = load_profile(search_from=[tmp_path])

    assert profile.disabled == frozenset({"G732-a", "G732-z"})


def test_explicit_source_wins_over_discovery(tmp_path: Path) -> None:
    write(tmp_path, "nk.toml", 'name = "Найденный"\n')
    chosen = write(tmp_path, "кафедра.toml", 'name = "Указанный"\n')

    assert load_profile(chosen, search_from=[tmp_path]).name == "Указанный"


def test_builtin_profile_has_no_source() -> None:
    assert load_profile().source is None


def test_unknown_key_inside_the_pyproject_section(tmp_path: Path) -> None:
    write(tmp_path, "pyproject.toml", '[tool.nk]\ndisabled = ["G732-a"]\n')

    with pytest.raises(ProfileError, match="неизвестные ключи"):
        load_profile(search_from=[tmp_path])


def test_broken_pyproject_is_not_skipped_silently(tmp_path: Path) -> None:
    write(tmp_path, "pyproject.toml", "[tool.nk]\nname = \n")

    with pytest.raises(ProfileError, match=r"pyproject\.toml"):
        load_profile(search_from=[tmp_path])


def test_origin_names_the_file_when_there_is_one(tmp_path: Path) -> None:
    path = write(tmp_path, "nk.toml", 'disable = ["G732-a"]\n')

    assert load_profile(path).origin == str(path)
    assert Profile(name="Кафедра N").origin == "Кафедра N"


def test_renamed_maps_previous_rule_ids() -> None:
    """Профиль кафедры переживает переименование правила."""
    profile = Profile(
        disabled=frozenset({"G732-6.5.7-caption-dot"}),
        params={"G732-6.5.7-caption-dot": {"a": 1}},
    )

    renamed = profile.renamed({"G732-6.5.7-caption-dot": "figure-caption-dot"})

    assert renamed.is_disabled("figure-caption-dot")
    assert renamed.params_for("figure-caption-dot") == {"a": 1}
