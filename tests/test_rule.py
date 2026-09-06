from collections.abc import Iterable
from pathlib import Path

import pytest
from support import make_document

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.profile import Profile
from nk.core.rule import (
    DuplicateRuleError,
    Rule,
    RuleRegistry,
    UnknownRuleError,
    rule,
)
from nk.core.standards import G732


def test_decorator_registers_rule_with_metadata(registry: RuleRegistry) -> None:
    @rule(
        id="G732-6.5.7-caption-dot",
        standards={G732: "6.5.7"},
        severity=Severity.ERROR,
        title="Подпись рисунка заканчивается точкой",
        registry=registry,
    )
    def caption_dot(doc: Document) -> Iterable[Finding]:
        return ()

    assert registry.get("G732-6.5.7-caption-dot") is caption_dot
    assert caption_dot.clause_for(G732.id) == "6.5.7"
    assert caption_dot.severity is Severity.ERROR
    assert isinstance(caption_dot, Rule)


def test_duplicate_id_is_an_error(registry: RuleRegistry) -> None:
    def declare() -> None:
        @rule(
            id="G732-дубль",
            standards={G732: "6.5.7"},
            severity=Severity.ERROR,
            title="Правило",
            registry=registry,
        )
        def some_rule(doc: Document) -> Iterable[Finding]:
            return ()

    declare()
    with pytest.raises(DuplicateRuleError, match="G732-дубль"):
        declare()


def test_unknown_rule_raises(registry: RuleRegistry) -> None:
    with pytest.raises(UnknownRuleError):
        registry.get("G732-нет-такого")


def test_registry_is_sorted_by_id(registry: RuleRegistry) -> None:
    for rule_id in ("G732-c", "G732-a", "G732-b"):

        @rule(
            id=rule_id,
            standards={G732: "6.1"},
            severity=Severity.INFO,
            title=rule_id,
            registry=registry,
        )
        def noop(doc: Document) -> Iterable[Finding]:
            return ()

    assert [impl.id for impl in registry.all()] == ["G732-a", "G732-b", "G732-c"]
    assert len(registry) == 3
    assert "G732-b" in registry


def _caption_dot_rule(registry: RuleRegistry):
    @rule(
        id="G732-6.5.7-caption-dot",
        standards={G732: "6.5.7"},
        severity=Severity.ERROR,
        title="Подпись рисунка заканчивается точкой",
        registry=registry,
    )
    def caption_dot(doc: Document) -> Iterable[Finding]:
        for line in doc.iter_lines():
            if "\\caption{" in line.stripped and line.stripped.rstrip().endswith("}"):
                text = line.stripped.rsplit("\\caption{", 1)[1].rstrip()[:-1]
                if text.endswith("."):
                    yield caption_dot.finding(
                        doc,
                        line,
                        message="Подпись рисунка заканчивается точкой.",
                        requirement="Наименование рисунка приводят без точки в конце.",
                        suggestion=f"\\caption{{{text[:-1]}}}",
                        col=line.raw.index("\\caption") + 1,
                    )

    return caption_dot


def test_finding_helper_fills_metadata_from_declaration(
    registry: RuleRegistry, document: Document
) -> None:
    caption_dot = _caption_dot_rule(registry)
    findings = list(caption_dot(document))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "G732-6.5.7-caption-dot"
    assert finding.clause == "6.5.7"
    assert finding.severity is Severity.ERROR
    assert finding.path == Path("report.tex")
    assert finding.lineno == 3
    assert finding.col == 3
    assert finding.excerpt == "  \\caption{Схема экспериментальной установки.}"
    assert len(finding.context) == 5
    assert finding.suggestion == "\\caption{Схема экспериментальной установки}"


def test_finding_severity_follows_profile_override(registry: RuleRegistry) -> None:
    caption_dot = _caption_dot_rule(registry)
    profile = Profile(severities={"G732-6.5.7-caption-dot": Severity.WARNING})
    doc = make_document("\\caption{Схема.}\n", profile=profile)

    findings = list(caption_dot(doc))
    assert [f.severity for f in findings] == [Severity.WARNING]


def test_params_merge_declaration_defaults_with_profile(registry: RuleRegistry) -> None:
    @rule(
        id="G732-5.3.2.1-keywords-count",
        standards={G732: "5.3.2.1"},
        severity=Severity.ERROR,
        title="Число ключевых слов вне допустимого диапазона",
        params={"keywords_min": 5, "keywords_max": 15},
        registry=registry,
    )
    def keywords_count(doc: Document) -> Iterable[Finding]:
        return ()

    doc = make_document(
        "текст\n",
        profile=Profile(params={"G732-5.3.2.1-keywords-count": {"keywords_max": 20}}),
    )
    assert keywords_count.params(doc) == {"keywords_min": 5, "keywords_max": 20}


def test_registry_collects_default_params(registry: RuleRegistry) -> None:
    @rule(
        id="G732-с-параметрами",
        standards={G732: "5.3.2.1"},
        severity=Severity.ERROR,
        title="Правило с параметрами",
        params={"limit": 3},
        registry=registry,
    )
    def with_params(doc: Document) -> Iterable[Finding]:
        return ()

    @rule(
        id="G732-без-параметров",
        standards={G732: "6.1"},
        severity=Severity.INFO,
        title="Правило без параметров",
        registry=registry,
    )
    def without_params(doc: Document) -> Iterable[Finding]:
        return ()

    assert registry.default_params() == {"G732-с-параметрами": {"limit": 3}}
