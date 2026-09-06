"""Сокращение «табл.» в ссылке на таблицу."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import reference_abbreviation

SHORT_FORM = re.compile(r"\bтабл\.\s*~?\s*(?:\d|\\(?:ref|autoref|cref))", re.IGNORECASE)


@rule(
    id="table-reference-word",
    standards={G732: "6.6.2"},
    severity=Severity.WARNING,
    title="В ссылке на таблицу использовано сокращение «табл.»",
    deprecated_ids=("G732-6.6.2-reference-word",),
)
def table_reference_word(doc: Document) -> Iterable[Finding]:
    """Ищет в тексте сокращение «табл.» перед номером или ссылкой.

    ## Почему это нарушение

    При ссылке пишут слово «таблица» полностью и её номер.

    ## Как исправить

    Заменить «табл.» на «таблица» в нужном падеже.
    """
    return reference_abbreviation(
        table_reference_word,
        doc,
        SHORT_FORM,
        message="В ссылке на таблицу использовано сокращение «табл.».",
        requirement="При ссылке пишут слово «таблица» полностью и её номер.",
        suggestion="Заменить «табл.» на «таблица» в нужном падеже.",
    )
