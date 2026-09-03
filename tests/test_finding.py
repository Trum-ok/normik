from pathlib import Path

from nk.core.finding import MAX_EXCERPT_LENGTH, Finding, Severity, truncate_excerpt


def test_severity_ordering() -> None:
    assert Severity.ERROR.rank < Severity.WARNING.rank < Severity.INFO.rank


def test_at_least_filters_by_threshold() -> None:
    assert Severity.ERROR.at_least(Severity.WARNING)
    assert Severity.WARNING.at_least(Severity.WARNING)
    assert not Severity.INFO.at_least(Severity.WARNING)


def test_severity_is_serialised_as_plain_string() -> None:
    assert f"{Severity.ERROR}" == "error"


def test_truncate_excerpt_keeps_short_lines() -> None:
    assert truncate_excerpt("  \\caption{Схема}") == "  \\caption{Схема}"


def test_truncate_excerpt_cuts_long_lines() -> None:
    result = truncate_excerpt("я" * 200)
    assert len(result) == MAX_EXCERPT_LENGTH
    assert result.endswith("…")


def test_findings_sort_by_path_then_line_then_rule() -> None:
    def make(path: str, lineno: int, rule_id: str) -> Finding:
        return Finding(
            rule_id=rule_id,
            clause="6.5.7",
            severity=Severity.ERROR,
            message="сообщение",
            requirement="требование",
            path=Path(path),
            lineno=lineno,
        )

    findings = [
        make("b.tex", 1, "G732-b"),
        make("a.tex", 10, "G732-b"),
        make("a.tex", 10, "G732-a"),
        make("a.tex", 2, "G732-z"),
    ]
    order = [(str(f.path), f.lineno, f.rule_id) for f in sorted(findings, key=lambda f: f.sort_key)]
    assert order == [
        ("a.tex", 2, "G732-z"),
        ("a.tex", 10, "G732-a"),
        ("a.tex", 10, "G732-b"),
        ("b.tex", 1, "G732-b"),
    ]
