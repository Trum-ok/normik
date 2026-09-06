"""Сокращение «рис.» в ссылке на иллюстрацию."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import reference_abbreviation

#: «рис. 1», «рис.~\ref{...}» — сокращение перед номером.
SHORT_FORM = re.compile(r"\bрис\.\s*~?\s*(?:\d|\\(?:ref|autoref|cref))", re.IGNORECASE)


@rule(
    id="figure-reference-word",
    standards={G732: "6.5.1", GR2105: "6.9.3"},
    severity=Severity.WARNING,
    title="В ссылке на иллюстрацию использовано сокращение «рис.»",
    deprecated_ids=("G732-6.5.1-reference-word",),
)
def figure_reference_word(doc: Document) -> Iterable[Finding]:
    """Ищет в тексте сокращение «рис.» перед номером или ссылкой.

    ## Почему это нарушение

    При ссылке пишут слово «рисунок» полностью и его номер: сокращение в ссылке
    не применяется.

    ## Как исправить

    Заменить «рис.» на «рисунок» в нужном падеже. Если на кафедре сокращение
    принято, правило отключается профилем.
    """
    return reference_abbreviation(
        figure_reference_word,
        doc,
        SHORT_FORM,
        message="В ссылке на иллюстрацию использовано сокращение «рис.».",
        requirement="При ссылке пишут слово «рисунок» полностью и его номер.",
        suggestion="Заменить «рис.» на «рисунок» в нужном падеже.",
    )
