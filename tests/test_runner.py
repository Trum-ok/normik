from collections.abc import Iterable
from pathlib import Path

from support import make_document

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import RuleRegistry, rule
from nk.core.runner import run


def finding(rule_id: str, lineno: int, severity: Severity = Severity.ERROR) -> Finding:
    return Finding(
        rule_id=rule_id,
        clause="6.5.7",
        severity=severity,
        message="сообщение",
        requirement="требование",
        path=Path("report.tex"),
        lineno=lineno,
    )


def declare(registry: RuleRegistry, rule_id: str, produce) -> None:
    @rule(
        id=rule_id,
        clause="6.5.7",
        severity=Severity.ERROR,
        title=rule_id,
        registry=registry,
    )
    def implementation(doc: Document) -> Iterable[Finding]:
        return produce()


def test_findings_are_sorted_deterministically(registry: RuleRegistry) -> None:
    declare(registry, "G732-b", lambda: [finding("G732-b", 10), finding("G732-b", 2)])
    declare(registry, "G732-a", lambda: [finding("G732-a", 10)])

    result = run(make_document("а\nб\n"), registry.all())

    assert [(f.lineno, f.rule_id) for f in result.findings] == [
        (2, "G732-b"),
        (10, "G732-a"),
        (10, "G732-b"),
    ]


def test_failing_rule_does_not_stop_the_run(registry: RuleRegistry) -> None:
    def explode() -> Iterable[Finding]:
        raise ValueError("сломалось")

    declare(registry, "G732-падает", explode)
    declare(registry, "G732-работает", lambda: [finding("G732-работает", 1)])

    result = run(make_document("а\n"), registry.all())

    assert [f.rule_id for f in result.findings] == ["G732-работает"]
    assert [f.rule_id for f in result.failed_rules] == ["G732-падает"]
    assert "ValueError: сломалось" in result.failed_rules[0].error


def test_findings_of_a_failing_rule_are_dropped(registry: RuleRegistry) -> None:
    def half_broken() -> Iterable[Finding]:
        yield finding("G732-падает", 1)
        raise ValueError("на середине")

    declare(registry, "G732-падает", half_broken)

    result = run(make_document("а\n"), registry.all())

    assert result.findings == ()
    assert len(result.failed_rules) == 1


def test_severity_threshold_hides_lower_levels(registry: RuleRegistry) -> None:
    declare(
        registry,
        "G732-разное",
        lambda: [
            finding("G732-разное", 1, Severity.ERROR),
            finding("G732-разное", 2, Severity.WARNING),
            finding("G732-разное", 3, Severity.INFO),
        ],
    )

    result = run(make_document("а\nб\nв\n"), registry.all(), threshold=Severity.WARNING)

    assert [f.severity for f in result.findings] == [Severity.ERROR, Severity.WARNING]
    assert result.summary == {Severity.ERROR: 1, Severity.WARNING: 1, Severity.INFO: 0}


def test_extra_findings_join_the_result(registry: RuleRegistry) -> None:
    result = run(
        make_document("а\n"),
        registry.all(),
        extra_findings=[finding("NK-PARSE-001", 1, Severity.INFO)],
    )

    assert [f.rule_id for f in result.findings] == ["NK-PARSE-001"]


def test_has_errors_reflects_exit_code(registry: RuleRegistry) -> None:
    declare(registry, "G732-warn", lambda: [finding("G732-warn", 1, Severity.WARNING)])
    assert not run(make_document("а\n"), registry.all()).has_errors

    declare(registry, "G732-err", lambda: [finding("G732-err", 1, Severity.ERROR)])
    assert run(make_document("а\n"), registry.all()).has_errors


def test_files_checked_counts_document_files() -> None:
    result = run(make_document("а\n"), ())
    assert result.files_checked == 1
    assert result.profile == "base"
