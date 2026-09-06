"""Форма ссылки на номер формулы."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732

#: «в формуле 1», «по формуле~\ref{eq:x}» — номер приводится без скобок.
BARE_REFERENCE = re.compile(r"формул\w*\s*~?\s*(?:\d|(?P<ref>\\ref)\b)", re.IGNORECASE)


@rule(
    id="G732-6.8.4-formula-reference-format",
    standards={G732: "6.8.4"},
    severity=Severity.ERROR,
    title="Номер формулы в ссылке приведён без скобок",
    fixable=True,
)
def formula_reference_format(doc: Document) -> Iterable[Finding]:
    r"""Ищет ссылки на номер формулы, приведённые без скобок: «в формуле 1»,
    «по формуле~\ref{eq:x}».

    ## Почему это нарушение

    Ссылки на порядковые номера формул приводят в скобках: в формуле (1).
    Номер без скобок сливается с текстом и не отличается от номера раздела.

    ## Как исправить

    Взять номер в скобки. В LaTeX для этого есть `\eqref`: он подставляет
    скобки сам.
    """
    for line in doc.iter_lines():
        match = BARE_REFERENCE.search(line.stripped)
        if match is None:
            continue
        # Замена \\ref на \\eqref однозначна; номер, вписанный цифрой,
        # в скобки автоматически не берётся: рядом может стоять что угодно.
        reference = match.span("ref")
        fix = (
            Fix(
                Region.in_line(line.path, line.lineno, reference[0] + 1, reference[1] + 1),
                "\\eqref",
            )
            if reference[0] >= 0
            else None
        )
        yield formula_reference_format.finding(
            doc,
            line,
            message="Номер формулы в ссылке приведён без скобок.",
            requirement="Ссылки на порядковые номера формул приводят в скобках: в формуле (1).",
            suggestion="Взять номер в скобки либо использовать \\eqref вместо \\ref.",
            col=match.start() + 1,
            fix=fix,
        )
