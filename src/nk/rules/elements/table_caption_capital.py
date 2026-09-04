"""Наименование таблицы со строчной буквы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    TABLE_ENVIRONMENTS,
    capitalize_first,
    caption_text,
    captions,
    first_letter,
    render_caption,
)


@rule(
    id="G732-6.6.3-caption-capital",
    clause="6.6.3",
    severity=Severity.ERROR,
    title="Наименование таблицы начинается со строчной буквы",
    fixable=True,
)
def table_caption_capital(doc: Document) -> Iterable[Finding]:
    """Проверяет первую букву наименования таблицы.

    ## Почему это нарушение

    Наименование таблицы приводят с прописной буквы без точки в конце.

    ## Как исправить

    Начать наименование с прописной буквы.
    """
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            letter = first_letter(text)
            if not letter or not letter.islower():
                continue
            yield table_caption_capital.finding(
                doc,
                command.span,
                message=f"Наименование таблицы начинается со строчной буквы «{letter}».",
                requirement="Наименование таблицы приводят с прописной буквы без точки в конце.",
                suggestion=render_caption(command, capitalize_first(text)),
                col=command.col,
                fix=command.region,
            )
