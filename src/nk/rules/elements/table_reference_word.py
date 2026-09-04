"""Сокращение «табл.» в ссылке на таблицу."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

SHORT_FORM = re.compile(r"\bтабл\.\s*~?\s*(?:\d|\\(?:ref|autoref|cref))", re.IGNORECASE)


@rule(
    id="G732-6.6.2-reference-word",
    clause="6.6.2",
    severity=Severity.WARNING,
    title="В ссылке на таблицу использовано сокращение «табл.»",
)
def table_reference_word(doc: Document) -> Iterable[Finding]:
    """Ищет в тексте сокращение «табл.» перед номером или ссылкой.

    ## Почему это нарушение

    При ссылке пишут слово «таблица» полностью и её номер.

    ## Как исправить

    Заменить «табл.» на «таблица» в нужном падеже.
    """
    for line in doc.iter_lines():
        match = SHORT_FORM.search(line.stripped)
        if match is None:
            continue
        yield table_reference_word.finding(
            doc,
            line,
            message="В ссылке на таблицу использовано сокращение «табл.».",
            requirement="При ссылке пишут слово «таблица» полностью и её номер.",
            suggestion="Заменить «табл.» на «таблица» в нужном падеже.",
            col=match.start() + 1,
        )
