"""Точка в конце наименования таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import TABLE_ENVIRONMENTS, caption_text, captions, one_line, render_caption


@rule(
    id="G732-6.6.3-caption-dot",
    clause="6.6.3",
    severity=Severity.ERROR,
    title="Наименование таблицы заканчивается точкой",
    fixable=True,
)
def table_caption_dot(doc: Document) -> Iterable[Finding]:
    r"""Проверяет наименование таблицы на точку в конце.

    ## Почему это нарушение

    Наименование таблицы приводят с прописной буквы без точки в конце.

    ## Как исправить

    Убрать точку в конце `\caption`.
    """
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            if not text.endswith("."):
                continue
            yield table_caption_dot.finding(
                doc,
                command.span,
                message="Наименование таблицы заканчивается точкой.",
                requirement="Наименование таблицы приводят с прописной буквы без точки в конце.",
                suggestion=render_caption(command, one_line(text[:-1])),
                col=command.col,
                fix=command.region,
            )
