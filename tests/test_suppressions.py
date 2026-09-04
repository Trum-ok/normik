from pathlib import Path

import pytest

from nk.core.finding import Finding, Severity
from nk.parse.suppressions import collect
from nk.parse.tex import parse


def make_finding(path: Path, lineno: int) -> Finding:
    return Finding(
        rule_id="G732-x",
        clause="6.5.7",
        severity=Severity.ERROR,
        message="m",
        requirement="r",
        path=path,
        lineno=lineno,
    )


def lines_of(tmp_path: Path, text: str) -> tuple:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document.lines


def test_bare_directive_covers_every_rule(tmp_path: Path) -> None:
    (item,) = collect(lines_of(tmp_path, "\\caption{Схема.} % nk: ignore\n")).items

    assert item.scope == "line"
    assert item.lineno == 1
    assert item.rule_ids == frozenset()


def test_directive_with_rule_ids(tmp_path: Path) -> None:
    (item,) = collect(
        lines_of(
            tmp_path,
            "\\caption{Схема.} % nk: ignore G732-6.5.7-caption-dot, G732-6.5.8-caption-capital\n",
        )
    ).items

    assert item.rule_ids == {"G732-6.5.7-caption-dot", "G732-6.5.8-caption-capital"}


def test_reason_is_separated_from_ids(tmp_path: Path) -> None:
    (item,) = collect(
        lines_of(
            tmp_path,
            "\\caption{Схема.} % nk: ignore G732-6.5.7-caption-dot -- на кафедре так принято\n",
        )
    ).items

    assert item.rule_ids == {"G732-6.5.7-caption-dot"}
    assert item.reason == "на кафедре так принято"


def test_ignore_file_scope(tmp_path: Path) -> None:
    (item,) = collect(
        lines_of(tmp_path, "% nk: ignore-file G732-6.5.1-reference-word\nтекст\n")
    ).items

    assert item.scope == "file"
    assert item.rule_ids == {"G732-6.5.1-reference-word"}


def test_escaped_percent_is_not_a_directive(tmp_path: Path) -> None:
    assert collect(lines_of(tmp_path, "доля 50\\% nk: ignore\n")).items == ()


def test_directive_in_text_without_comment_is_ignored(tmp_path: Path) -> None:
    assert collect(lines_of(tmp_path, "\\caption{nk: ignore внутри текста}\n")).items == ()


@pytest.mark.parametrize(
    "text",
    ["%nk:ignore\n", "%   nk : ignore  \n", "% NK: ignore\n"],
)
def test_spacing_variants(tmp_path: Path, text: str) -> None:
    items = collect(lines_of(tmp_path, text)).items
    assert len(items) == (0 if "NK" in text else 1)


def test_line_scope_covers_only_its_line(tmp_path: Path) -> None:
    (item,) = collect(lines_of(tmp_path, "текст\n\\caption{Схема.} % nk: ignore\n")).items

    report = tmp_path / "report.tex"
    assert item.covers(make_finding(report, 2))
    assert not item.covers(make_finding(report, 1))


def test_file_scope_covers_any_line(tmp_path: Path) -> None:
    (item,) = collect(lines_of(tmp_path, "% nk: ignore-file\nтекст\n")).items
    assert item.covers(make_finding(tmp_path / "report.tex", 99))


def test_unused_tracks_matches(tmp_path: Path) -> None:
    suppressions = collect(lines_of(tmp_path, "а % nk: ignore\nб % nk: ignore\n"))
    suppressions.match(make_finding(tmp_path / "report.tex", 1))

    assert [item.lineno for item in suppressions.unused()] == [2]
