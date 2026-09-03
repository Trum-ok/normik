"""Перенос слова в заголовке рубрики."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_text, headings

HYPHENATION_MARKER = "\\-"


@rule(
    id="G732-6.2.4-heading-hyphenation",
    clause="6.2.4",
    severity=Severity.ERROR,
    title="В заголовке задан перенос слова",
)
def heading_hyphenation(doc: Document) -> Iterable[Finding]:
    for command in headings(doc):
        if HYPHENATION_MARKER not in heading_text(command):
            continue
        yield heading_hyphenation.finding(
            doc,
            command.span,
            message="В заголовке задана точка переноса «\\-».",
            requirement="Переносы слов в заголовках не допускаются.",
            suggestion="Убрать «\\-» из заголовка.",
            col=command.col,
        )
