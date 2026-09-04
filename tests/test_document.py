from pathlib import Path

from support import make_document

from nk.core.document import Document, Line, Span
from nk.parse.tex import parse


def test_line_at_returns_requested_line(document: Document) -> None:
    line = document.line_at(Path("report.tex"), 3)
    assert line is not None
    assert line.raw == "  \\caption{Схема экспериментальной установки.}"


def test_line_at_outside_range_is_none(document: Document) -> None:
    assert document.line_at(Path("report.tex"), 99) is None
    assert document.line_at(Path("report.tex"), 0) is None
    assert document.line_at(Path("другой.tex"), 1) is None


def test_context_includes_two_lines_around(document: Document) -> None:
    assert document.context(Path("report.tex"), 3) == (
        "\\begin{figure}[h]",
        "  \\includegraphics{img/setup.png}",
        "  \\caption{Схема экспериментальной установки.}",
        "\\end{figure}",
        "Текст после рисунка.",
    )


def test_context_is_clipped_at_file_boundaries(document: Document) -> None:
    assert len(document.context(Path("report.tex"), 1)) == 3
    assert len(document.context(Path("report.tex"), 5)) == 3


def test_lines_of_separates_files() -> None:
    first = make_document("один\n", path="a.tex")
    lines = (
        *first.lines,
        Line(path=Path("b.tex"), lineno=1, raw="два", stripped="два"),
    )
    doc = Document(root=Path("."), files=(Path("a.tex"), Path("b.tex")), lines=lines)
    assert [line.raw for line in doc.lines_of(Path("a.tex"))] == ["один"]
    assert [line.raw for line in doc.lines_of(Path("b.tex"))] == ["два"]


def test_blank_line_detection() -> None:
    doc = make_document("текст\n   \n")
    assert not doc.lines[0].is_blank
    assert doc.lines[1].is_blank


def test_span_contains() -> None:
    span = Span(path=Path("report.tex"), start=2, end=4)
    assert span.contains(2)
    assert span.contains(4)
    assert not span.contains(5)


def parsed(tmp_path: Path, text: str) -> Document:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document


def test_covered_lines_index_lines_inside_named_environments(tmp_path: Path) -> None:
    document = parsed(
        tmp_path,
        "текст\n\\begin{table}\n\\begin{tabular}{c}\nа\n\\end{tabular}\n\\end{table}\nтекст\n",
    )
    path = tmp_path / "report.tex"

    assert document.structure.covered_lines("tabular") == frozenset(
        {(path, 3), (path, 4), (path, 5)}
    )
    assert document.structure.covered_lines("tabular") is document.structure.covered_lines(
        "tabular"
    )
    assert document.structure.covered_lines("figure") == frozenset()


def test_ordered_commands_follow_the_report_order_and_are_cached(tmp_path: Path) -> None:
    document = parsed(
        tmp_path, "\\section{А}\n\\begin{figure}\n\\label{f}\n\\end{figure}\n\\ref{f}\n"
    )

    ordered = document.ordered_commands()

    assert [command.name for command in ordered] == ["section", "label", "ref"]
    assert document.ordered_commands() is ordered


def test_memo_builds_once() -> None:
    document = make_document("текст\n")
    calls: list[int] = []

    def build() -> int:
        calls.append(1)
        return 42

    assert document.memo("ключ", build) == 42
    assert document.memo("ключ", build) == 42
    assert len(calls) == 1
