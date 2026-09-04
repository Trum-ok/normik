"""Висящий предлог: короткое слово не привязано к следующему."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import NBSP
from nk.rules._text import is_code, prose

#: Однобуквенные предлоги и союзы: их не оставляют в конце строки никогда.
ONE_LETTER = "в к с о у а и"

#: Двухбуквенные предлоги, союзы и проклитическая частица «не».
TWO_LETTERS = "во за из ко на не ни но об от по со до"

#: Трёхбуквенные предлоги и союзы.
THREE_LETTERS = "без для как над при про под что или чем"

#: Слова, привязываемые к следующему. Частицы «бы», «же», «ли» сюда не входят:
#: они примыкают к предыдущему слову, ими занимается NK-STYLE-particle-nbsp.
PROCLITICS = f"{ONE_LETTER} {TWO_LETTERS} {THREE_LETTERS}".split()

_PROCLITIC = re.compile(
    r"(?<![\w~-])(?:" + "|".join(PROCLITICS) + r")( )(?=[«\"\w\\$])",
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
    """Находит короткий предлог или союз, отделённый от следующего слова обычным пробелом.

    ## Почему это замечание

    Висящий предлог в конце строки — классическое замечание нормоконтроля.
    Где именно ляжет перенос, в исходнике не видно, поэтому предлог привязывают
    к следующему слову заранее, независимо от вёрстки.

    Проверяются одно-, двух- и трёхбуквенные предлоги и союзы. Длинные —
    «через», «между», «около» — в конце строки не выглядят оборванными,
    и правило их не трогает.

    ## Как исправить

    Поставить неразрывный пробел: `в~таблице`.

    !!! note

        Правило выключено по умолчанию: находок оно даёт много, а требование
        стандартом не установлено. Включается профилем через `enable`.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _PROCLITIC.finditer(prose(doc, line)):
            start, end = match.span(1)
            yield preposition_nbsp.finding(
                doc,
                line,
                message=f"Слово «{match.group(0).strip()}» не привязано к следующему.",
                requirement=(
                    "Короткие предлоги и союзы привязывают к следующему слову неразрывным "
                    "пробелом, чтобы они не оставались в конце строки."
                ),
                suggestion=f"Поставить неразрывный пробел: {NBSP}",
                col=start + 1,
                fix=Fix(Region.in_line(line.path, line.lineno, start + 1, end + 1), NBSP),
            )
