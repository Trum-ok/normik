"""Наименование рисунка со строчной буквы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    FIGURE_ENVIRONMENTS,
    capitalize_first,
    caption_text,
    captions,
    first_letter,
    render_caption,
)


@rule(
    id="G732-6.5.8-caption-capital",
    clause="6.5.8",
    severity=Severity.ERROR,
    title="Наименование рисунка начинается со строчной буквы",
    fixable=True,
)
def figure_caption_capital(doc: Document) -> Iterable[Finding]:
    """Проверяет первую букву наименования рисунка. Наименование, начинающееся
    с цифры или обозначения, не проверяется.

    ## Почему это нарушение

    Наименование рисунка приводят с прописной буквы без точки в конце.

    ## Как исправить

    Начать наименование с прописной буквы.
    """
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            letter = first_letter(text)
            if not letter or not letter.islower():
                continue
            yield figure_caption_capital.finding(
                doc,
                command.span,
                message=f"Наименование рисунка начинается со строчной буквы «{letter}».",
                requirement="Наименование рисунка приводят с прописной буквы без точки в конце.",
                suggestion=render_caption(command, capitalize_first(text)),
                col=command.col,
                fix=command.region,
            )
