from nk.core.finding import Severity
from nk.core.profile import Profile


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
