"""Короткое слово, не привязанное к следующему."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._text import is_code, prose

NBSP = "~"

#: Предлоги, союзы и частицы, которые не оставляют в конце строки.
SHORT_WORDS = [
    "в",
    "к",
    "с",
    "о",
    "у",
    "а",
    "и",
    "я",
    "за",
    "из",
    "на",
    "по",
    "до",
    "от",
    "об",
    "во",
    "со",
    "ко",
    "не",
    "ни",
    "но",
    "же",
    "бы",
    "ли",
    "то",
    "как",
    "что",
    "при",
    "для",
    "над",
    "под",
    "без",
    "через",
    "между",
    "около",
    "после",
    "перед",
    "про",
    "их",
    "её",
    "его",
]

_SHORT = re.compile(
    r"(?<![\w~-])(?:" + "|".join(SHORT_WORDS) + r")( )(?=[«\"\wА-Яа-яЁё\\$])",
    re.IGNORECASE,
)


@rule(
    id="NK-STYLE-preposition-nbsp",
    clause="",
    severity=Severity.INFO,
    title="Предлог не привязан к следующему слову",
    fixable=True,
    default_off=True,
)
def preposition_nbsp(doc: Document) -> Iterable[Finding]:
    """Находит предлог или союз, отделённый от следующего слова обычным пробелом.

    ## Почему это замечание

    Висящий предлог в конце строки — классическое замечание нормоконтроля.
    Где именно ляжет перенос, в исходнике не видно, поэтому предлог привязывают
    к следующему слову заранее, независимо от вёрстки.

    ## Как исправить

    Поставить неразрывный пробел: `в~таблице`.

    !!! note

        Правило выключено по умолчанию: находок оно даёт много, а требование
        стандартом не установлено. Включается профилем через `enable`.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _SHORT.finditer(prose(line)):
            start, end = match.span(1)
            yield preposition_nbsp.finding(
                doc,
                line,
                message=f"Слово «{match.group(0).strip()}» не привязано к следующему.",
                requirement=(
                    "Предлоги и союзы привязывают к следующему слову неразрывным пробелом, "
                    "чтобы они не оставались в конце строки."
                ),
                suggestion=f"Поставить неразрывный пробел: {NBSP}",
                col=start + 1,
                fix=Fix(Region.in_line(line.path, line.lineno, start + 1, end + 1), NBSP),
            )
