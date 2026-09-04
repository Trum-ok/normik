"""Дефис вместо тире в перечне: термин."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import TERMS_ELEMENTS
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import DASH, section_lines, structural_headings

SEPARATOR = re.compile(r"\S( - )\S")


@rule(
    id="G732-6.14-terms-dash",
    clause="6.14",
    severity=Severity.WARNING,
    title="В перечне терминов определение отделено дефисом",
    fixable=True,
)
def terms_dash(doc: Document) -> Iterable[Finding]:
    """Проверяет знак, отделяющий термин от расшифровки.

    ## Почему это нарушение

    Стандарт требует отделять правую часть тире. Дефис — другой знак, и в
    наборе он заметно короче.

    ## Как исправить

    Заменить дефис на тире.
    """
    for command, element in structural_headings(doc):
        if element not in TERMS_ELEMENTS:
            continue
        for line in section_lines(doc, command):
            match = SEPARATOR.search(line.stripped)
            if match is None:
                continue
            start, end = match.span(1)
            yield terms_dash.finding(
                doc,
                line,
                message="Расшифровка отделена дефисом, а не тире.",
                requirement="В перечне терминов определения приводят справа через тире.",
                suggestion=f"Заменить дефис на тире: {DASH}",
                col=start + 2,
                fix=Fix(
                    Region.in_line(line.path, line.lineno, start + 2, end),
                    DASH,
                ),
            )
