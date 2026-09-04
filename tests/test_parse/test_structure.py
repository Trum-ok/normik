from pathlib import Path

from support import make_document

from nk.core.document import Structure
from nk.parse.issues import ENVIRONMENT_ORPHAN_END, ENVIRONMENT_UNCLOSED, GROUP_UNCLOSED
from nk.parse.structure import build_structure

REPORT = Path("report.tex")


def scan(text: str) -> tuple[Structure, tuple[str, ...]]:
    structure, issues = build_structure(make_document(text).lines)
    return structure, tuple(issue.code for issue in issues)


def test_environment_span_covers_begin_and_end() -> None:
    structure, issues = scan(
        "\\begin{figure}[h]\n"
        "  \\includegraphics{img/setup.png}\n"
        "  \\caption{Схема установки}\n"
        "\\end{figure}\n"
    )

    assert issues == ()
    figure = next(structure.find_environments("figure"))
    assert figure.span.start == 1
    assert figure.span.end == 4
    assert figure.options == ("h",)


def test_commands_belong_to_the_enclosing_environment() -> None:
    structure, _ = scan(
        "\\section{Методика}\n\\begin{figure}\n  \\caption{Схема установки}\n\\end{figure}\n"
    )

    figure = next(structure.find_environments("figure"))
    assert [command.name for command in figure.commands] == ["caption"]
    assert [command.name for command in structure.commands] == ["section"]


def test_nested_environments_form_a_tree() -> None:
    structure, issues = scan(
        "\\begin{table}\n\\begin{tabular}{ll}\n  а & б \\\\\n\\end{tabular}\n\\end{table}\n"
    )

    assert issues == ()
    table = next(structure.find_environments("table"))
    assert [child.name for child in table.children] == ["tabular"]
    assert table.children[0].args == ("ll",)


def test_enclosing_finds_the_innermost_environment() -> None:
    structure, _ = scan(
        "\\begin{table}\n\\begin{tabular}{ll}\n  а & б\n\\end{tabular}\n\\end{table}\n"
    )

    innermost = structure.enclosing(REPORT, 3)
    assert innermost is not None
    assert innermost.name == "tabular"


def test_enclosing_outside_any_environment_is_none() -> None:
    structure, _ = scan("текст\n\\begin{figure}\n\\end{figure}\n")
    assert structure.enclosing(REPORT, 1) is None


def test_command_arguments_are_read_by_brace_balance() -> None:
    structure, issues = scan("\\caption{Схема \\textbf{с вложенной} группой}\n")

    assert issues == ()
    caption = next(structure.find_commands("caption"))
    assert caption.args == ("Схема \\textbf{с вложенной} группой",)
    assert caption.lineno == 1
    assert caption.col == 1


def test_multiline_argument_keeps_the_starting_position() -> None:
    structure, issues = scan("\\caption{Схема\n  экспериментальной установки}\nтекст\n")

    assert issues == ()
    caption = next(structure.find_commands("caption"))
    assert caption.args == ("Схема\n  экспериментальной установки",)
    assert caption.lineno == 1
    assert caption.span.end == 2


def test_escaped_brace_does_not_close_the_group() -> None:
    structure, _ = scan("\\caption{Доля 50\\% и \\{скобка\\}}\n")
    caption = next(structure.find_commands("caption"))
    assert caption.args == ("Доля 50\\% и \\{скобка\\}",)


def test_verbatim_content_is_not_scanned() -> None:
    structure, issues = scan(
        "\\begin{lstlisting}\n\\begin{figure}\nне окружение {\n\\end{lstlisting}\n"
    )

    assert issues == ()
    assert [env.name for env in structure.find_environments()] == ["lstlisting"]
    assert structure.environments[0].span.end == 4


def test_unclosed_environment_is_reported() -> None:
    structure, issues = scan("\\begin{figure}\n  \\caption{Схема}\nтекст\n")

    assert issues == (ENVIRONMENT_UNCLOSED,)
    figure = next(structure.find_environments("figure"))
    assert figure.span.end == 3


def test_orphan_end_is_reported_and_scanning_continues() -> None:
    structure, issues = scan("\\end{figure}\n\\section{Введение}\n")

    assert issues == (ENVIRONMENT_ORPHAN_END,)
    assert [command.name for command in structure.find_commands()] == ["section"]


def test_crossed_environments_are_recovered() -> None:
    structure, issues = scan(
        "\\begin{table}\n\\begin{tabular}{ll}\n\\end{table}\n\\section{Далее}\n"
    )

    assert issues == (ENVIRONMENT_UNCLOSED,)
    assert {env.name for env in structure.find_environments()} == {"table", "tabular"}
    assert [command.name for command in structure.find_commands()] == ["section"]


def test_unclosed_group_is_reported() -> None:
    _, issues = scan("\\caption{Схема установки\n")
    assert issues == (GROUP_UNCLOSED,)


def test_commands_inside_arguments_are_visible() -> None:
    structure, issues = scan(
        "\\caption{Схема\\label{fig:a}}\n"
        "См.\\footnote{рисунок~\\ref{fig:a}} и \\emph{\\cite{ivanov}}.\n"
    )

    assert issues == ()
    assert [c.name for c in structure.commands] == [
        "caption",
        "label",
        "footnote",
        "ref",
        "emph",
        "cite",
    ]
    label = next(structure.find_commands("label"))
    assert (label.lineno, label.col, label.args) == (1, 15, ("fig:a",))


def test_environment_inside_argument_is_scanned() -> None:
    structure, issues = scan("\\parbox{5cm}{\\begin{tabular}{c}\\label{tab:a}\\end{tabular}}\n")

    assert issues == ()
    tabular = next(structure.find_environments("tabular"))
    assert [c.name for c in tabular.commands] == ["label"]
    assert [c.name for c in structure.commands] == ["parbox"]


def test_macro_definition_body_is_not_scanned() -> None:
    structure, issues = scan(
        "\\newcommand{\\ssr}[1]{\\section*{#1}\\label{sec:#1}}\n"
        "\\renewcommand*{\\thefigure}{\\arabic{figure}}\n"
        "\\def\\figref#1{рисунок~\\ref{fig:#1}}\n"
        "\\newenvironment{box}{\\begin{center}}{\\end{center}}\n"
        "\\ssr{ВВЕДЕНИЕ}\n"
    )

    assert issues == ()
    assert [c.name for c in structure.commands] == [
        "newcommand",
        "renewcommand*",
        "def",
        "newenvironment",
        "ssr",
    ]
    assert list(structure.find_environments()) == []


def test_starred_commands_keep_the_star() -> None:
    structure, _ = scan("\\section*{ВВЕДЕНИЕ}\n")
    assert [command.name for command in structure.find_commands()] == ["section*"]


def test_structure_spans_several_files() -> None:
    lines = (
        *make_document("\\begin{figure}\n\\end{figure}\n", path="a.tex").lines,
        *make_document("\\begin{table}\n\\end{table}\n", path="b.tex").lines,
    )
    structure, issues = build_structure(list(lines))

    assert issues == ()
    assert {(env.name, env.path.name) for env in structure.find_environments()} == {
        ("figure", "a.tex"),
        ("table", "b.tex"),
    }
