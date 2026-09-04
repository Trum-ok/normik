"""Точка в конце наименования рисунка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, caption_text, captions, one_line


@rule(
    id="G732-6.5.7-caption-dot",
    clause="6.5.7",
    severity=Severity.ERROR,
    title="Наименование рисунка заканчивается точкой",
)
def figure_caption_dot(doc: Document) -> Iterable[Finding]:
    r"""Проверяет наименование рисунка на точку в конце. Точка внутри наименования
    нарушением не является.

    ## Почему это нарушение

    Наименование рисунка приводят с прописной буквы без точки в конце: оно
    образует с номером единую подпись, а не предложение.

    ## Как исправить

    Убрать точку в конце `\caption`.
    """
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            if not text.endswith("."):
                continue
            yield figure_caption_dot.finding(
                doc,
                command.span,
                message="Наименование рисунка заканчивается точкой.",
                requirement="Наименование рисунка приводят с прописной буквы без точки в конце.",
                suggestion=f"\\{command.name}{{{one_line(text[:-1])}}}",
                col=command.col,
            )
