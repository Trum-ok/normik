from collections.abc import Iterable

import pytest

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.profile import Profile, ProfileError
from nk.core.registry import load_rules, select_rules, validate_profile
from nk.core.rule import (
    REGISTRY,
    DuplicateRuleError,
    RuleDeclarationError,
    RuleRegistry,
    UnknownRuleError,
    rule,
)
from nk.core.standards import G732, GR2105, Origin


@pytest.fixture
def three_rules(registry: RuleRegistry) -> RuleRegistry:
    for rule_id in ("G732-a", "G732-b", "G732-c"):

        @rule(
            id=rule_id,
            standards={G732: "6.1"},
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
        origin=Origin.UNIVERSAL,
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
        origin=Origin.UNIVERSAL,
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
        origin=Origin.UNIVERSAL,
        severity=Severity.INFO,
        title="Шумное правило",
        default_off=True,
        registry=registry,
    )
    def noisy(doc: Document) -> Iterable[Finding]:
        return ()

    chosen = select_rules(registry, select=["NK-STYLE-шумное"])
    assert [impl.id for impl in chosen] == ["NK-STYLE-шумное"]


def test_rule_of_another_standard_does_not_run(registry: RuleRegistry) -> None:
    @rule(
        id="требование-2.105",
        standards={GR2105: "6.9.4"},
        severity=Severity.INFO,
        title="Требование одного стандарта",
        registry=registry,
    )
    def eskd_only(doc: Document) -> Iterable[Finding]:
        return ()

    assert select_rules(registry, profile=Profile(standard=G732)) == ()


def test_universal_rule_runs_under_a_standard_without_its_clause(registry: RuleRegistry) -> None:
    """Пункт называет, где требование записано, а не сужает область правила."""

    @rule(
        id="универсальное",
        standards={GR2105: "6.16.6"},
        origin=Origin.UNIVERSAL,
        severity=Severity.INFO,
        title="Универсальное требование с пунктом одного стандарта",
        registry=registry,
    )
    def everywhere(doc: Document) -> Iterable[Finding]:
        return ()

    chosen = select_rules(registry, profile=Profile(standard=G732))

    assert [impl.id for impl in chosen] == ["универсальное"]


def test_regulation_rule_runs_under_any_standard(registry: RuleRegistry) -> None:
    @rule(
        id="по-положению",
        origin=Origin.REGULATION,
        severity=Severity.INFO,
        title="Требование положения",
        registry=registry,
    )
    def regulation(doc: Document) -> Iterable[Finding]:
        return ()

    for standard in (G732, GR2105):
        chosen = select_rules(registry, profile=Profile(standard=standard))
        assert [impl.id for impl in chosen] == ["по-положению"], standard.id


def test_standard_requirement_without_clauses_is_rejected(registry: RuleRegistry) -> None:
    """Пустая карта раньше молча означала типографику: так терялось происхождение."""
    with pytest.raises(RuleDeclarationError, match="без пунктов"):

        @rule(
            id="ничьё",
            severity=Severity.INFO,
            title="Требование без пунктов и без происхождения",
            registry=registry,
        )
        def nobodys(doc: Document) -> Iterable[Finding]:
            return ()


def test_regulation_requirement_with_clauses_is_rejected(registry: RuleRegistry) -> None:
    """Пункт положения объявляет профиль: чужой нумерации в реестре не место."""
    with pytest.raises(RuleDeclarationError, match="пункты"):

        @rule(
            id="положение-с-пунктом",
            standards={G732: "6.1"},
            origin=Origin.REGULATION,
            severity=Severity.INFO,
            title="Требование положения с пунктом стандарта",
            registry=registry,
        )
        def mixed(doc: Document) -> Iterable[Finding]:
            return ()


def test_deprecated_id_resolves_to_the_rule() -> None:
    registry = load_rules()

    assert registry.get("G732-6.5.7-caption-dot").id == "figure-caption-dot"
    assert "G732-6.5.7-caption-dot" in registry
    assert registry.canonical("G732-6.5.7-caption-dot") == "figure-caption-dot"


def test_every_deprecated_id_resolves() -> None:
    """Прежнее имя обязано вести к живому правилу, иначе оно только вводит в заблуждение."""
    registry = load_rules()

    broken = [old for old, new in registry.aliases.items() if new not in registry]

    assert broken == []


def test_deprecated_id_can_be_selected() -> None:
    registry = load_rules()

    chosen = select_rules(registry, select=["G732-6.5.7-caption-dot"])

    assert [impl.id for impl in chosen] == ["figure-caption-dot"]


def test_deprecated_id_colliding_with_a_rule_is_rejected() -> None:
    registry = RuleRegistry()

    @rule(
        id="занято",
        standards={G732: "6.1"},
        severity=Severity.INFO,
        title="Первое",
        registry=registry,
    )
    def first(doc: Document) -> Iterable[Finding]:
        return ()

    with pytest.raises(DuplicateRuleError, match="занят правилом"):

        @rule(
            id="второе",
            standards={G732: "6.1"},
            severity=Severity.INFO,
            title="Второе",
            deprecated_ids=("занято",),
            registry=registry,
        )
        def second(doc: Document) -> Iterable[Finding]:
            return ()
