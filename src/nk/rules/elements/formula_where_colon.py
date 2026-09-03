"""Двоеточие после слова «где» в пояснении к формуле."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

WHERE_WITH_COLON = re.compile(r"^\s*где\s*:", re.IGNORECASE)


@rule(
    id="G732-6.8.2-where-colon",
    clause="6.8.2",
    severity=Severity.ERROR,
    title="Пояснение к формуле начинается со слова «где» с двоеточием",
)
def formula_where_colon(doc: Document) -> Iterable[Finding]:
    for line in doc.iter_lines():
        match = WHERE_WITH_COLON.match(line.stripped)
        if match is None:
            continue
        yield formula_where_colon.finding(
            doc,
            line,
            message="После слова «где» стоит двоеточие.",
            requirement="Первую строку пояснения к формуле начинают со слова «где» без двоеточия.",
            suggestion="Убрать двоеточие после «где».",
            col=match.end() - 1 + 1,
        )
