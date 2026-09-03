"""Точка в конце перечня ключевых слов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import keyword_lists


@rule(
    id="G732-6.12.2-keywords-final-dot",
    clause="6.12.2",
    severity=Severity.ERROR,
    title="Перечень ключевых слов заканчивается точкой",
)
def keywords_final_dot(doc: Document) -> Iterable[Finding]:
    for line, keywords in keyword_lists(doc):
        if not keywords or not keywords[-1].endswith("."):
            continue
        yield keywords_final_dot.finding(
            doc,
            line,
            message="Перечень ключевых слов заканчивается точкой.",
            requirement="Перечень ключевых слов приводят без точки в конце.",
            suggestion=f"Убрать точку после «{keywords[-1][:-1]}».",
        )
