"""Частица, оторванная от предыдущего слова."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import NBSP
from nk.rules._text import is_code, prose

#: Частицы, примыкающие к предыдущему слову.
ENCLITICS = ("же", "бы", "ли")

_ENCLITIC = re.compile(r"(?<=\w)( )(?:" + "|".join(ENCLITICS) + r")(?![\w~-])", re.IGNORECASE)


@rule(
    id="NK-STYLE-particle-nbsp",
    clause="",
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
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _ENCLITIC.finditer(prose(doc, line)):
            start, end = match.span(1)
            yield particle_nbsp.finding(
                doc,
                line,
                message=f"Частица «{match.group(0).strip()}» оторвана от предыдущего слова.",
                requirement=(
                    "Частицы «же», «бы» и «ли» примыкают к предыдущему слову: "
                    "неразрывный пробел ставят перед ними."
                ),
                suggestion=f"Поставить неразрывный пробел перед частицей: {NBSP}",
                col=start + 1,
                fix=Fix(Region.in_line(line.path, line.lineno, start + 1, end + 1), NBSP),
            )
