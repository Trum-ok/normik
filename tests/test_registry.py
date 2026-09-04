from collections.abc import Iterable

import pytest

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.profile import Profile, ProfileError
from nk.core.registry import load_rules, select_rules, validate_profile
from nk.core.rule import REGISTRY, RuleRegistry, UnknownRuleError, rule


@pytest.fixture
def three_rules(registry: RuleRegistry) -> RuleRegistry:
    for rule_id in ("G732-a", "G732-b", "G732-c"):

        @rule(
            id=rule_id,
            clause="6.1",
            severity=Severity.INFO,
            title=rule_id,
            registry=registry,
        )
        def noop(doc: Document) -> Iterable[Finding]:
            return ()

    return registry


def test_select_all_by_default(three_rules: RuleRegistry) -> None:
    assert [impl.id for impl in select_rules(three_rules)] == ["G732-a", "G732-b", "G732-c"]


def test_select_narrows_the_set(three_rules: RuleRegistry) -> None:
    chosen = select_rules(three_rules, select=["G732-c", "G732-a"])
    assert [impl.id for impl in chosen] == ["G732-a", "G732-c"]


def test_ignore_subtracts(three_rules: RuleRegistry) -> None:
    chosen = select_rules(three_rules, ignore=["G732-b"])
    assert [impl.id for impl in chosen] == ["G732-a", "G732-c"]


def test_profile_disable_subtracts(three_rules: RuleRegistry) -> None:
    chosen = select_rules(three_rules, profile=Profile(disabled=frozenset({"G732-a"})))
    assert [impl.id for impl in chosen] == ["G732-b", "G732-c"]


def test_ignore_wins_over_select(three_rules: RuleRegistry) -> None:
    chosen = select_rules(three_rules, select=["G732-a", "G732-b"], ignore=["G732-a"])
    assert [impl.id for impl in chosen] == ["G732-b"]


def test_unknown_id_in_select_is_an_error(three_rules: RuleRegistry) -> None:
    with pytest.raises(UnknownRuleError, match="G732-нет"):
        select_rules(three_rules, select=["G732-нет"])


def test_unknown_id_in_ignore_is_an_error(three_rules: RuleRegistry) -> None:
    with pytest.raises(UnknownRuleError, match="G732-нет"):
        select_rules(three_rules, ignore=["G732-нет"])


def test_load_rules_walks_the_package_without_errors() -> None:
    assert load_rules() is REGISTRY


def test_validate_profile_accepts_known_rules(three_rules: RuleRegistry) -> None:
    profile = Profile(
        disabled=frozenset({"G732-a"}),
        severities={"G732-b": Severity.WARNING},
    )
    validate_profile(profile, three_rules)


def test_validate_profile_rejects_typos(three_rules: RuleRegistry) -> None:
    profile = Profile(name="Кафедра N", disabled=frozenset({"G732-ф"}))

    with pytest.raises(ProfileError, match="G732-ф"):
        validate_profile(profile, three_rules)


def test_default_off_rule_is_skipped(registry: RuleRegistry) -> None:
    @rule(
        id="NK-STYLE-шумное",
        clause="",
        severity=Severity.INFO,
        title="Шумное правило",
        default_off=True,
        registry=registry,
    )
    def noisy(doc: Document) -> Iterable[Finding]:
        return ()

    assert select_rules(registry) == ()


def test_profile_enables_a_default_off_rule(registry: RuleRegistry) -> None:
    @rule(
        id="NK-STYLE-шумное",
        clause="",
        severity=Severity.INFO,
        title="Шумное правило",
        default_off=True,
        registry=registry,
    )
    def noisy(doc: Document) -> Iterable[Finding]:
        return ()

    chosen = select_rules(registry, profile=Profile(enabled=frozenset({"NK-STYLE-шумное"})))
    assert [impl.id for impl in chosen] == ["NK-STYLE-шумное"]


def test_select_overrides_default_off(registry: RuleRegistry) -> None:
    @rule(
        id="NK-STYLE-шумное",
        clause="",
        severity=Severity.INFO,
        title="Шумное правило",
        default_off=True,
        registry=registry,
    )
    def noisy(doc: Document) -> Iterable[Finding]:
        return ()

    chosen = select_rules(registry, select=["NK-STYLE-шумное"])
    assert [impl.id for impl in chosen] == ["NK-STYLE-шумное"]
