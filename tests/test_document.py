from pathlib import Path

from conftest import make_document

from nk.core.document import Document, Line, Span


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
