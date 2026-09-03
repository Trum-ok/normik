"""Точка в конце наименования рисунка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

CAPTION_COMMANDS = frozenset({"caption", "caption*"})
FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*"})


@rule(
    id="G732-6.5.7-caption-dot",
    clause="6.5.7",
    severity=Severity.ERROR,
    title="Наименование рисунка заканчивается точкой",
)
def figure_caption_dot(doc: Document) -> Iterable[Finding]:
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        for command in environment.all_commands():
            if command.name not in CAPTION_COMMANDS:
                continue
            text = command.arg.strip()
            if not text.endswith("."):
                continue
            yield figure_caption_dot.finding(
                doc,
                command.span,
                message="Наименование рисунка заканчивается точкой.",
                requirement="Наименование рисунка приводят с прописной буквы без точки в конце.",
                suggestion=f"\\{command.name}{{{_one_line(text[:-1])}}}",
                col=command.col,
            )


def _one_line(text: str) -> str:
    """Свернуть наименование в одну строку: в LaTeX перевод строки внутри группы — пробел."""
    return " ".join(text.split())
