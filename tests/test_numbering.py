from pathlib import Path

from nk.core.numbering import EQUATION, FIGURE, TABLE, Scheme
from nk.parse.tex import parse


def numbering(tmp_path: Path, text: str):
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document.numbering


FIGURE_SOURCE = """\
\\section{Первый}
\\begin{figure}\\includegraphics{a}\\end{figure}
\\section{Второй}
\\begin{figure}\\includegraphics{b}\\end{figure}
"""


def test_continuous_numbering_by_default(tmp_path: Path) -> None:
    items = numbering(tmp_path, FIGURE_SOURCE).by_kind(FIGURE)

    assert [item.number for item in items] == ["1", "2"]
    assert all(item.scheme is Scheme.CONTINUOUS for item in items)


def test_counterwithin_switches_to_section_numbering(tmp_path: Path) -> None:
    items = numbering(tmp_path, "\\counterwithin{figure}{section}\n" + FIGURE_SOURCE).by_kind(
        FIGURE
    )

    assert [item.number for item in items] == ["1.1", "2.1"]


def test_renewcommand_with_thesection_switches_too(tmp_path: Path) -> None:
    source = "\\renewcommand{\\thefigure}{\\thesection.\\arabic{figure}}\n" + FIGURE_SOURCE
    assert [item.number for item in numbering(tmp_path, source).by_kind(FIGURE)] == ["1.1", "2.1"]


def test_renewcommand_without_thesection_stays_continuous(tmp_path: Path) -> None:
    source = "\\renewcommand{\\thefigure}{\\arabic{figure}}\n" + FIGURE_SOURCE
    assert [item.number for item in numbering(tmp_path, source).by_kind(FIGURE)] == ["1", "2"]


APPENDIX_SOURCE = """\
\\section{Методика}
\\begin{figure}\\includegraphics{a}\\end{figure}
\\section*{ПРИЛОЖЕНИЕ А}
\\begin{figure}\\includegraphics{b}\\end{figure}
\\section*{ПРИЛОЖЕНИЕ Б}
\\begin{figure}\\includegraphics{c}\\end{figure}
"""


def test_continuous_counter_runs_through_appendices(tmp_path: Path) -> None:
    items = numbering(tmp_path, APPENDIX_SOURCE).by_kind(FIGURE)

    assert [item.number for item in items] == ["1", "2", "3"]
    assert [item.appendix for item in items] == ["", "А", "Б"]


def test_section_scheme_gives_appendix_designation(tmp_path: Path) -> None:
    items = numbering(tmp_path, "\\counterwithin{figure}{section}\n" + APPENDIX_SOURCE).by_kind(
        FIGURE
    )

    assert [item.number for item in items] == ["1.1", "А.1", "Б.1"]


def test_appendix_command_switches_sections_to_letters(tmp_path: Path) -> None:
    source = (
        "\\counterwithin{figure}{section}\n"
        "\\section{Методика}\n"
        "\\begin{figure}\\includegraphics{a}\\end{figure}\n"
        "\\appendix\n"
        "\\section{Протоколы}\n"
        "\\begin{figure}\\includegraphics{b}\\end{figure}\n"
    )
    assert [item.number for item in numbering(tmp_path, source).by_kind(FIGURE)] == ["1.1", "А.1"]


def test_kinds_are_counted_separately(tmp_path: Path) -> None:
    source = (
        "\\begin{figure}\\includegraphics{a}\\end{figure}\n"
        "\\begin{table}\\begin{tabular}{l}а\\end{tabular}\\end{table}\n"
        "\\begin{figure}\\includegraphics{b}\\end{figure}\n"
        "\\begin{equation}x\\end{equation}\n"
    )
    result = numbering(tmp_path, source)

    assert [item.number for item in result.by_kind(FIGURE)] == ["1", "2"]
    assert [item.number for item in result.by_kind(TABLE)] == ["1"]
    assert [item.number for item in result.by_kind(EQUATION)] == ["1"]


def test_starred_math_is_not_numbered(tmp_path: Path) -> None:
    source = "\\begin{equation*}x\\end{equation*}\n\\begin{equation}y\\end{equation}\n"
    assert [item.number for item in numbering(tmp_path, source).by_kind(EQUATION)] == ["1"]


def test_scheme_changes_are_recorded(tmp_path: Path) -> None:
    source = (
        "\\counterwithin{figure}{section}\n"
        "\\renewcommand{\\thefigure}{\\arabic{figure}}\n"
        "\\begin{figure}\\includegraphics{a}\\end{figure}\n"
    )
    changes = numbering(tmp_path, source).changes_of(FIGURE)

    assert [change.scheme for change in changes] == [Scheme.BY_SECTION, Scheme.CONTINUOUS]
    assert [change.lineno for change in changes] == [1, 2]


def test_title_reads_as_the_reader_sees_it(tmp_path: Path) -> None:
    items = numbering(tmp_path, "\\counterwithin{figure}{section}\n" + APPENDIX_SOURCE).by_kind(
        FIGURE
    )
    assert items[1].title == "Рисунок А.1"
