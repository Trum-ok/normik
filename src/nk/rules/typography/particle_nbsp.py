"""Частица, оторванная от предыдущего слова."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import NBSP
from nk.rules._text import gaps

#: Частицы, примыкающие к предыдущему слову.
ENCLITICS = ("же", "бы", "ли")

_ENCLITIC = re.compile(r"(?<=\w)( )(?:" + "|".join(ENCLITICS) + r")(?![\w~-])", re.IGNORECASE)


@rule(
    id="NK-STYLE-particle-nbsp",
    severity=Severity.INFO,
    title="Частица не привязана к предыдущему слову",
    fixable=True,
)
def particle_nbsp(doc: Document) -> Iterable[Finding]:
    """Находит частицу «же», «бы» или «ли», отделённую от предыдущего слова.

    ## Почему это замечание

    В отличие от предлога, эти частицы примыкают к слову слева: в конце строки
    не должно оставаться слово, от которого частицу оторвал перенос. Поэтому
    неразрывный пробел ставится перед частицей, а не после неё.

    ## Как исправить

    Поставить неразрывный пробел слева: `отличался~бы`, `так~ли`.
    """
    for gap in gaps(doc, _ENCLITIC):
        yield particle_nbsp.finding(
            doc,
            gap.line,
            message=f"Частица «{gap.found}» оторвана от предыдущего слова.",
            requirement=(
                "Частицы «же», «бы» и «ли» примыкают к предыдущему слову: "
                "неразрывный пробел ставят перед ними."
            ),
            suggestion=f"Поставить неразрывный пробел перед частицей: {NBSP}",
            col=gap.col,
            fix=gap.fix,
        )
