"""Наименование таблицы со строчной буквы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import TABLE_ENVIRONMENTS, caption_text, captions, first_letter


@rule(
    id="G732-6.6.3-caption-capital",
    clause="6.6.3",
    severity=Severity.ERROR,
    title="Наименование таблицы начинается со строчной буквы",
)
def table_caption_capital(doc: Document) -> Iterable[Finding]:
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        for command in captions(environment):
            letter = first_letter(caption_text(command))
            if not letter or not letter.islower():
                continue
            yield table_caption_capital.finding(
                doc,
                command.span,
                message=f"Наименование таблицы начинается со строчной буквы «{letter}».",
                requirement="Наименование таблицы приводят с прописной буквы без точки в конце.",
                suggestion=f"Начать наименование с прописной буквы: «{letter.upper()}».",
                col=command.col,
            )
