"""Наименование таблицы со строчной буквы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import TABLE_ENVIRONMENTS, capitalize_first, caption_findings, first_letter


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

    def check(text: str) -> tuple[str, str] | None:
        letter = first_letter(text)
        if not letter or not letter.islower():
            return None
        message = f"Наименование таблицы начинается со строчной буквы «{letter}»."
        return message, capitalize_first(text)

    return caption_findings(
        table_caption_capital,
        doc,
        TABLE_ENVIRONMENTS,
        requirement="Наименование таблицы приводят с прописной буквы без точки в конце.",
        check=check,
    )
