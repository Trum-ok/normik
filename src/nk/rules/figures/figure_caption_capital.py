"""Наименование рисунка со строчной буквы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import FIGURE_ENVIRONMENTS, capitalize_first, caption_findings, first_letter


@rule(
    id="figure-caption-capital",
    standards={G732: "6.5.8"},
    severity=Severity.ERROR,
    title="Наименование рисунка начинается со строчной буквы",
    fixable=True,
    deprecated_ids=("G732-6.5.8-caption-capital",),
)
def figure_caption_capital(doc: Document) -> Iterable[Finding]:
    """Проверяет первую букву наименования рисунка. Наименование, начинающееся
    с цифры или обозначения, не проверяется.

    ## Почему это нарушение

    Наименование рисунка приводят с прописной буквы без точки в конце.

    ## Как исправить

    Начать наименование с прописной буквы.
    """

    def check(text: str) -> tuple[str, str] | None:
        letter = first_letter(text)
        if not letter or not letter.islower():
            return None
        message = f"Наименование рисунка начинается со строчной буквы «{letter}»."
        return message, capitalize_first(text)

    return caption_findings(
        figure_caption_capital,
        doc,
        FIGURE_ENVIRONMENTS,
        requirement="Наименование рисунка приводят с прописной буквы без точки в конце.",
        check=check,
    )
