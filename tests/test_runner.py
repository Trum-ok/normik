from collections.abc import Iterable
from pathlib import Path

from support import make_document

from nk.core.baseline import Baseline
from nk.core.diagnostics import IGNORE_UNKNOWN, IGNORE_UNUSED, INPUT_MISSING
from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import RuleRegistry, rule
from nk.core.runner import run
from nk.core.standards import G732
from nk.parse.tex import parse, parse_findings


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
        standards={G732: "6.5.7"},
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


def test_inline_suppression_hides_the_finding(registry: RuleRegistry, tmp_path: Path) -> None:
    declare(registry, "G732-точка", lambda: [])
    path = tmp_path / "report.tex"
    path.write_text("\\caption{Схема.} % nk: ignore G732-точка\n", encoding="utf-8")
    parsed = parse([path])

    result = run(
        parsed.document,
        (),
        extra_findings=[
            Finding(
                rule_id="G732-точка",
                clause="6.5.7",
                severity=Severity.ERROR,
                message="сообщение",
                requirement="требование",
                path=path,
                lineno=1,
            )
        ],
        suppressions=parsed.suppressions,
    )

    assert [f.rule_id for f in result.findings] == []
    assert result.suppressed.inline == 1
    assert not result.has_errors


def test_suppression_for_another_rule_does_not_hide(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\caption{Схема.} % nk: ignore G732-другое\n", encoding="utf-8")
    parsed = parse([path])

    result = run(
        parsed.document,
        (),
        extra_findings=[
            Finding(
                rule_id="G732-точка",
                clause="6.5.7",
                severity=Severity.ERROR,
                message="сообщение",
                requirement="требование",
                path=path,
                lineno=1,
            )
        ],
        suppressions=parsed.suppressions,
    )

    assert [f.rule_id for f in result.findings if f.rule_id.startswith("G732")] == ["G732-точка"]
    assert result.suppressed.inline == 0


def test_unused_suppression_is_reported(registry: RuleRegistry, tmp_path: Path) -> None:
    declare(registry, "G732-точка", lambda: [])
    path = tmp_path / "report.tex"
    path.write_text("\\caption{Схема} % nk: ignore G732-точка\n", encoding="utf-8")
    parsed = parse([path])

    result = run(parsed.document, registry.all(), suppressions=parsed.suppressions)

    assert [f.rule_id for f in result.findings] == [IGNORE_UNUSED]
    assert result.findings[0].lineno == 1


def test_unknown_rule_in_suppression_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("текст % nk: ignore G732-нет-такого\n", encoding="utf-8")
    parsed = parse([path])

    result = run(
        parsed.document,
        (),
        suppressions=parsed.suppressions,
        known_ids=frozenset({"G732-есть"}),
    )

    assert [f.rule_id for f in result.findings] == [IGNORE_UNKNOWN]


def test_unused_is_silent_for_rules_that_did_not_run(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("текст % nk: ignore G732-выключено\n", encoding="utf-8")
    parsed = parse([path])

    result = run(parsed.document, (), suppressions=parsed.suppressions)

    assert result.findings == ()


def test_ignored_internal_code_is_dropped(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\input{нет-такого}\n", encoding="utf-8")
    parsed = parse([path])

    result = run(
        parsed.document,
        (),
        extra_findings=parse_findings(parsed),
        ignored=frozenset({INPUT_MISSING}),
    )

    assert result.findings == ()


def test_baseline_hides_known_findings(registry: RuleRegistry) -> None:
    declare(registry, "G732-точка", lambda: [finding("G732-точка", 1)])
    document = make_document("а\n")
    first = run(document, registry.all())

    second = run(document, registry.all(), baseline=Baseline.of(first.findings))

    assert second.findings == ()
    assert second.suppressed.baseline == 1
    assert not second.has_errors


def test_baseline_lets_new_findings_through(registry: RuleRegistry) -> None:
    declare(registry, "G732-точка", lambda: [finding("G732-точка", 1)])
    document = make_document("а\nб\n")
    snapshot = Baseline.of(run(document, registry.all()).findings)

    registry.clear()
    declare(registry, "G732-точка", lambda: [finding("G732-точка", 1), finding("G732-точка", 2)])
    result = run(document, registry.all(), baseline=snapshot)

    assert [f.lineno for f in result.findings] == [2]
    assert result.suppressed.baseline == 1


def test_threshold_is_applied_after_suppression(registry: RuleRegistry, tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("а % nk: ignore\nб\n", encoding="utf-8")
    parsed = parse([path])
    findings = [
        Finding(
            rule_id="G732-точка",
            clause="6.5.7",
            severity=Severity.INFO,
            message="m",
            requirement="r",
            path=path,
            lineno=lineno,
        )
        for lineno in (1, 2)
    ]

    result = run(
        parsed.document,
        (),
        extra_findings=findings,
        suppressions=parsed.suppressions,
        threshold=Severity.WARNING,
    )

    assert result.findings == ()
    assert result.suppressed.inline == 1
