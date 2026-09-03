"""Регистр ключевых слов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import keyword_lists


@rule(
    id="G732-6.12.2-keywords-uppercase",
    clause="6.12.2",
    severity=Severity.ERROR,
    title="Ключевые слова набраны не прописными буквами",
)
def keywords_uppercase(doc: Document) -> Iterable[Finding]:
    for line, keywords in keyword_lists(doc):
        lowercase = [word for word in keywords if word != word.upper()]
        if not lowercase:
            continue
        yield keywords_uppercase.finding(
            doc,
            line,
            message=f"Ключевые слова набраны не прописными: {', '.join(lowercase[:3])}.",
            requirement=(
                "Ключевые слова приводят в именительном падеже прописными буквами, "
                "в строку, через запятые."
            ),
            suggestion=f"Записать прописными: {', '.join(word.upper() for word in keywords)}.",
        )
