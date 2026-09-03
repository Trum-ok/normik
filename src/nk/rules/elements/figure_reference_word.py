"""Сокращение «рис.» в ссылке на иллюстрацию."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

#: «рис. 1», «рис.~\ref{...}» — сокращение перед номером.
SHORT_FORM = re.compile(r"\bрис\.\s*~?\s*(?:\d|\\(?:ref|autoref|cref))", re.IGNORECASE)


@rule(
    id="G732-6.5.1-reference-word",
    clause="6.5.1",
    severity=Severity.WARNING,
    title="В ссылке на иллюстрацию использовано сокращение «рис.»",
)
def figure_reference_word(doc: Document) -> Iterable[Finding]:
    for line in doc.iter_lines():
        match = SHORT_FORM.search(line.stripped)
        if match is None:
            continue
        yield figure_reference_word.finding(
            doc,
            line,
            message="В ссылке на иллюстрацию использовано сокращение «рис.».",
            requirement="При ссылке пишут слово «рисунок» полностью и его номер.",
            suggestion="Заменить «рис.» на «рисунок» в нужном падеже.",
            col=match.start() + 1,
        )
