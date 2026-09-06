"""Двоеточие после слова «где» в пояснении к формуле."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._text import is_code

WHERE_WITH_COLON = re.compile(r"^\s*где\s*:", re.IGNORECASE)


@rule(
    id="formula-where-colon",
    standards={G732: "6.8.2", GR2105: "6.10.1"},
    severity=Severity.ERROR,
    title="Пояснение к формуле начинается со слова «где» с двоеточием",
    fixable=True,
    deprecated_ids=("G732-6.8.2-where-colon",),
)
def formula_where_colon(doc: Document) -> Iterable[Finding]:
    """Ищет строку, начинающуюся со слова «где» с двоеточием.

    ## Почему это нарушение

    Первую строку пояснения к формуле начинают со слова «где» без двоеточия,
    далее идут обозначения с расшифровкой.

    ## Как исправить

    Убрать двоеточие после «где». Листинги и таблицы правило не
    просматривает: там это содержимое кода или ячейки.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        match = WHERE_WITH_COLON.match(line.stripped)
        if match is None:
            continue
        colon = match.end()
        yield formula_where_colon.finding(
            doc,
            line,
            message="После слова «где» стоит двоеточие.",
            requirement="Первую строку пояснения к формуле начинают со слова «где» без двоеточия.",
            suggestion="Убрать двоеточие после «где».",
            col=colon,
            fix=Fix(Region.in_line(line.path, line.lineno, colon, colon + 1), ""),
        )
