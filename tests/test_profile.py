from pathlib import Path

import pytest

from nk.core.finding import Severity
from nk.core.profile import Profile, ProfileError, load_profile


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_empty_profile_changes_nothing() -> None:
    profile = Profile()
    assert not profile.is_disabled("G732-6.5.7-caption-dot")
    assert profile.severity_for("G732-6.5.7-caption-dot", Severity.ERROR) is Severity.ERROR
    assert profile.params_for("G732-6.5.7-caption-dot") == {}


def test_disable_and_severity_override() -> None:
    profile = Profile(
        name="Кафедра N",
        disabled=frozenset({"G732-4-required-elements"}),
        severities={"G732-6.2.4-heading-hyphenation": Severity.WARNING},
    )
    assert profile.is_disabled("G732-4-required-elements")
    assert (
        profile.severity_for("G732-6.2.4-heading-hyphenation", Severity.ERROR) is Severity.WARNING
    )


def test_resolve_merges_defaults_with_overrides() -> None:
    profile = Profile(params={"G732-5.3.2.1-keywords-count": {"keywords_max": 20}})
    resolved = profile.resolve(
        {"G732-5.3.2.1-keywords-count": {"keywords_min": 5, "keywords_max": 15}}
    )
    assert resolved.params_for("G732-5.3.2.1-keywords-count") == {
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


def test_two_levels_of_extends_are_rejected(tmp_path: Path) -> None:
    write(tmp_path, "дед.toml", 'name = "Дед"\n')
    write(tmp_path, "отец.toml", 'name = "Отец"\nextends = "дед"\n')
    child = write(tmp_path, "сын.toml", 'name = "Сын"\nextends = "отец"\n')

    with pytest.raises(ProfileError, match="один уровень"):
        load_profile(child)


def test_self_extends_is_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, "сам.toml", 'name = "Сам"\nextends = "сам"\n')

    with pytest.raises(ProfileError, match="один уровень"):
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
    path = write(tmp_path, "кафедра.toml", 'enable = ["NK-STYLE-preposition-nbsp"]\n')

    profile = load_profile(path)

    assert profile.is_enabled("NK-STYLE-preposition-nbsp")
    assert "NK-STYLE-preposition-nbsp" in profile.mentioned_rules()


def test_enable_accumulates_through_extends(tmp_path: Path) -> None:
    write(tmp_path, "родитель.toml", 'enable = ["NK-STYLE-a"]\n')
    child = write(tmp_path, "ребёнок.toml", 'extends = "родитель"\nenable = ["NK-STYLE-b"]\n')

    assert load_profile(child).enabled == frozenset({"NK-STYLE-a", "NK-STYLE-b"})
