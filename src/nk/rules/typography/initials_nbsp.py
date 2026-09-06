"""Инициалы, оторванные от фамилии."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import NBSP
from nk.rules._text import is_code, prose

#: Пара инициалов подряд: «И. И.». Одиночный инициал не ищем — он неотличим
#: от однобуквенного обозначения в конце предложения: «...в приложении А. В работе...».
INITIALS = re.compile(r"(?<![\w.])[А-ЯЁA-Z]\.( +)[А-ЯЁA-Z]\.")
_SURNAME = re.compile(r"[А-ЯЁA-Z][а-яёa-z]")


@rule(
    id="initials-nbsp",
    severity=Severity.INFO,
    title="Инициалы не привязаны к фамилии",
    fixable=True,
    deprecated_ids=("NK-STYLE-initials-nbsp",),
)
def initials_nbsp(doc: Document) -> Iterable[Finding]:
    """Находит обычный пробел между инициалами и фамилией.

    ## Почему это замечание

    Перенос, разрывающий «И. И.» и «Иванова», выглядит ошибкой набора: фамилия
    с инициалами читается как единое обозначение.

    ## Как исправить

    Поставить неразрывные пробелы: `И.~И.~Иванов` или `Иванов~И.~И.`

    Одиночный инициал правило не ищет: он неотличим от однобуквенного
    обозначения в конце предложения — «приведено в приложении А. В работе…».
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        text = prose(doc, line)
        for match in INITIALS.finditer(text):
            for start, end in _spaces(text, match):
                yield initials_nbsp.finding(
                    doc,
                    line,
                    message="Инициалы отделены от соседнего слова обычным пробелом.",
                    requirement="Инициалы и фамилию связывают неразрывным пробелом.",
                    suggestion=f"Поставить неразрывный пробел: {NBSP}",
                    col=start + 1,
                    fix=Fix(Region.in_line(line.path, line.lineno, start + 1, end + 1), NBSP),
                )


def _spaces(text: str, match: re.Match[str]) -> list[tuple[int, int]]:
    """Пробелы внутри группы инициалов и по той стороне, где стоит фамилия."""
    inner = match.span(1)

    after = match.end()
    if text[after : after + 1] == " " and _SURNAME.match(text[after + 1 : after + 3]):
        # Порядок «И. И. Иванов»: слово слева к инициалам не относится.
        return [inner, (after, after + 1)]

    leading = _leading_space(text, match.start())
    return [leading, inner] if leading is not None else [inner]


def _leading_space(text: str, start: int) -> tuple[int, int] | None:
    """Пробел между фамилией и инициалами в порядке «Иванов И. И.»."""
    if start < 1 or text[start - 1] != " ":
        return None
    end = start - 1
    begin = end
    while begin > 0 and text[begin - 1].isalpha():
        begin -= 1
    word = text[begin:end]
    return (end, end + 1) if word[:1].isupper() and len(word) > 1 else None
