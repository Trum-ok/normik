"""Форма ссылки на номер формулы."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

#: «в формуле 1», «по формуле~\ref{eq:x}» — номер приводится без скобок.
BARE_REFERENCE = re.compile(r"формул\w*\s*~?\s*(?:\d|\\ref\b)", re.IGNORECASE)


@rule(
    id="G732-6.8.4-formula-reference-format",
    clause="6.8.4",
    severity=Severity.ERROR,
    title="Номер формулы в ссылке приведён без скобок",
)
def formula_reference_format(doc: Document) -> Iterable[Finding]:
    for line in doc.iter_lines():
        match = BARE_REFERENCE.search(line.stripped)
        if match is None:
            continue
        yield formula_reference_format.finding(
            doc,
            line,
            message="Номер формулы в ссылке приведён без скобок.",
            requirement="Ссылки на порядковые номера формул приводят в скобках: в формуле (1).",
            suggestion="Взять номер в скобки либо использовать \\eqref вместо \\ref.",
            col=match.start() + 1,
        )
