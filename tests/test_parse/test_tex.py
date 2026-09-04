from pathlib import Path

import pytest

from nk.core.diagnostics import ENCODING_FALLBACK, INPUT_CYCLE, INPUT_MISSING
from nk.parse.tex import collect_sources, parse, parse_findings, read_file, strip_comment


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("текст % комментарий", "текст "),
        ("% весь комментарий", ""),
        ("доля 50\\% годовых", "доля 50\\% годовых"),
        ("доля 50\\% % и комментарий", "доля 50\\% "),
        ("перенос \\\\% комментарий", "перенос \\\\"),
        ("без комментария", "без комментария"),
        ("\\verb|a % b| и дальше", "\\verb|a % b| и дальше"),
        ("\\verb|a % b| % комментарий", "\\verb|a % b| "),
        ("\\verb*+50%+ текст", "\\verb*+50%+ текст"),
        ("\\verb |a % b| текст", "\\verb |a % b| текст"),
        ("\\verbatiminput{f} % комментарий", "\\verbatiminput{f} "),
        ("\\verb|незакрытый % текст", "\\verb|незакрытый % текст"),
    ],
)
def test_strip_comment(raw: str, expected: str) -> None:
    assert strip_comment(raw) == expected


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_read_file_keeps_raw_and_strips_comment(tmp_path: Path) -> None:
    path = write(tmp_path, "report.tex", "\\section{Введение} % заголовок\nтекст\n")
    lines, issues = read_file(path)

    assert issues == ()
    assert lines[0].raw == "\\section{Введение} % заголовок"
    assert lines[0].stripped == "\\section{Введение} "
    assert lines[1].lineno == 2


def test_verbatim_content_keeps_percent(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        "report.tex",
        "\\begin{verbatim}\nprint(50 % 7)  # остаток\n\\end{verbatim}\nтекст % хвост\n",
    )
    lines, _ = read_file(path)

    assert lines[1].stripped == "print(50 % 7)  # остаток"
    assert lines[3].stripped == "текст "


def test_cp1251_file_is_read_with_an_issue(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_bytes("\\section{Введение}\n".encode("cp1251"))
    lines, issues = read_file(path)

    assert [issue.code for issue in issues] == [ENCODING_FALLBACK]
    assert lines[0].raw == "\\section{Введение}"


def test_input_is_expanded_and_positions_point_to_the_source(tmp_path: Path) -> None:
    write(tmp_path, "chapters/02-method.tex", "\\section{Методика}\nтекст главы\n")
    root = write(tmp_path, "report.tex", "\\documentclass{article}\n\\input{chapters/02-method}\n")

    result = parse([root])

    assert result.issues == ()
    assert result.document.files == (root, tmp_path / "chapters/02-method.tex")
    included = result.document.lines_of(tmp_path / "chapters/02-method.tex")
    assert [line.lineno for line in included] == [1, 2]
    assert included[0].raw == "\\section{Методика}"


def test_include_with_explicit_extension(tmp_path: Path) -> None:
    write(tmp_path, "часть.tex", "текст\n")
    root = write(tmp_path, "report.tex", "\\include{часть.tex}\n")

    result = parse([root])
    assert result.issues == ()
    assert tmp_path / "часть.tex" in result.document.files


def test_missing_input_is_reported_and_does_not_stop_parsing(tmp_path: Path) -> None:
    root = write(tmp_path, "report.tex", "\\input{нет-такого}\n\\section{Введение}\n")

    result = parse([root])

    assert [issue.code for issue in result.issues] == [INPUT_MISSING]
    assert result.issues[0].lineno == 1
    assert result.issues[0].col == 1
    assert len(result.document.lines) == 2


def test_include_cycle_is_reported_once(tmp_path: Path) -> None:
    write(tmp_path, "a.tex", "\\input{b}\n")
    write(tmp_path, "b.tex", "\\input{a}\n")
    root = write(tmp_path, "report.tex", "\\input{a}\n")

    result = parse([root])

    assert [issue.code for issue in result.issues] == [INPUT_CYCLE]
    assert {path.name for path in result.document.files} == {"report.tex", "a.tex", "b.tex"}


def test_file_included_twice_is_read_once(tmp_path: Path) -> None:
    write(tmp_path, "общее.tex", "текст\n")
    root = write(tmp_path, "report.tex", "\\input{общее}\n\\input{общее}\n")

    result = parse([root])

    assert result.document.files.count(tmp_path / "общее.tex") == 1


def test_input_inside_comment_is_ignored(tmp_path: Path) -> None:
    root = write(tmp_path, "report.tex", "% \\input{нет-такого}\n")

    result = parse([root])
    assert result.issues == ()


def test_collect_sources_expands_directory(tmp_path: Path) -> None:
    write(tmp_path, "b.tex", "")
    write(tmp_path, "a.tex", "")
    write(tmp_path, "img/note.txt", "")

    assert [path.name for path in collect_sources([tmp_path])] == ["a.tex", "b.tex"]


def test_parse_findings_carry_excerpt_and_context(tmp_path: Path) -> None:
    root = write(tmp_path, "report.tex", "первая\n\\input{нет-такого}\nтретья\n")

    findings = parse_findings(parse([root]))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == INPUT_MISSING
    assert finding.severity == "info"
    assert finding.excerpt == "\\input{нет-такого}"
    assert finding.context == ("первая", "\\input{нет-такого}", "третья")


def test_directory_is_expanded_from_the_main_file(tmp_path: Path) -> None:
    """Порядок отчёта задают включения, а не алфавит имён файлов."""
    write(tmp_path, "введение.tex", "\\section*{ВВЕДЕНИЕ}\n")
    write(tmp_path, "заключение.tex", "\\section*{ЗАКЛЮЧЕНИЕ}\n")
    write(
        tmp_path,
        "отчёт.tex",
        "\\begin{document}\n\\include{введение}\n\\include{заключение}\n\\end{document}\n",
    )

    result = parse([tmp_path])

    assert [path.name for path in result.document.files] == [
        "отчёт.tex",
        "введение.tex",
        "заключение.tex",
    ]


def test_file_outside_the_main_document_goes_after_it(tmp_path: Path) -> None:
    write(tmp_path, "черновик.tex", "\\section{Набросок}\n")
    write(tmp_path, "отчёт.tex", "\\begin{document}\n\\section{Раздел}\n\\end{document}\n")

    result = parse([tmp_path])

    assert [path.name for path in result.document.files] == ["отчёт.tex", "черновик.tex"]
