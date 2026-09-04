from pathlib import Path

from nk.parse.tex import parse


def headings(tmp_path: Path, text: str):
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document.headings


def test_own_commands_are_known(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\section{Раздел}\n")

    assert scheme.depth_of("section") == 1
    assert scheme.depth_of("subsection") == 2
    assert scheme.is_numbered("section")
    assert not scheme.is_numbered("section*")


def test_newcommand_alias_becomes_a_heading(tmp_path: Path) -> None:
    scheme = headings(
        tmp_path,
        "\\newcommand{\\ssr}[1]{\\section*{\\centering #1}}\n\\ssr{ВВЕДЕНИЕ}\n",
    )

    assert scheme.depth_of("ssr") == 1
    assert scheme.alias_of("ssr") == "section*"
    assert not scheme.is_numbered("ssr")


def test_def_alias_becomes_a_heading(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\def\\subsec#1{\\subsection{#1}}\n\\subsec{Методика}\n")

    assert scheme.depth_of("subsec") == 2
    assert scheme.is_numbered("subsec")


def test_alias_of_an_alias_is_resolved(tmp_path: Path) -> None:
    scheme = headings(
        tmp_path,
        "\\newcommand{\\ssr}[1]{\\section*{#1}}\n\\newcommand{\\element}[1]{\\ssr{#1}}\n",
    )

    assert scheme.alias_of("element") == "section*"


def test_macro_without_a_parameter_is_not_a_heading(tmp_path: Path) -> None:
    """Подставить текст такого заголовка в находку нечем, поэтому он не опознаётся."""
    scheme = headings(tmp_path, "\\newcommand{\\intro}{\\section*{ВВЕДЕНИЕ}}\n\\intro\n")

    assert "intro" not in scheme


def test_macro_without_a_heading_inside_is_not_a_heading(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\newcommand{\\highlight}[1]{\\textbf{#1}}\n")

    assert "highlight" not in scheme


def test_chapters_shift_the_remaining_levels(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\chapter{Глава}\n\\section{Раздел}\n")

    assert scheme.depth_of("chapter") == 1
    assert scheme.depth_of("section") == 2
    assert scheme.depth_of("subsection") == 3


def test_document_without_chapters_keeps_section_at_the_top(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\section{Раздел}\n\\subsection{Подраздел}\n")

    assert scheme.depth_of("section") == 1
    assert scheme.depth_of("subsection") == 2


def test_macro_that_spends_the_parameter_elsewhere_is_not_a_heading(tmp_path: Path) -> None:
    scheme = headings(tmp_path, "\\newcommand{\\example}[1]{\\subsection*{Пример}#1}\n")

    assert "example" not in scheme
