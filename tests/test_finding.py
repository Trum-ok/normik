from pathlib import Path

from nk.core.finding import MAX_EXCERPT_LENGTH, Finding, Severity, excerpt_window, truncate_excerpt


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


def test_short_line_is_left_alone() -> None:
    assert excerpt_window("короткая строка", 3) == ("короткая строка", 0)


def test_long_line_without_a_column_is_cut_from_the_start() -> None:
    text, offset = excerpt_window("x" * 300, None)

    assert offset == 0
    assert text.startswith("x") and text.endswith("…")
    assert len(text) == MAX_EXCERPT_LENGTH


def test_violation_beyond_the_limit_stays_visible() -> None:
    """Иначе находка о двухсотом знаке показывает зачин строки и ничем не помогает."""
    line = "a" * 200 + "цель" + "b" * 200
    col = 201

    text, offset = excerpt_window(line, col)

    assert text[col - 1 - offset :].startswith("цель")
    assert len(text) <= MAX_EXCERPT_LENGTH


def test_window_is_marked_on_both_sides() -> None:
    text, _ = excerpt_window("a" * 400, 300)

    assert text.startswith("…") and text.endswith("…")


def test_window_does_not_run_past_the_end() -> None:
    """У нарушения в самом конце окно упирается в конец строки, а не выходит за него."""
    line = "a" * 200 + "ц"

    text, offset = excerpt_window(line, len(line))

    assert text.endswith("ц")
    assert text[len(line) - 1 - offset] == "ц"
