"""Единица величины при обеих границах диапазона."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._text import PHYSICAL_UNITS, is_code, prose

_UNIT = "(?:" + "|".join(sorted(PHYSICAL_UNITS, key=len, reverse=True)) + ")"

#: Диапазон, у первой границы которого стоит своя единица: «от 1 мм до 5 мм».
_RANGE = re.compile(
    r"\b[Оо]т\s+\d[\d,.]*\s*~?\s*(?P<unit>" + _UNIT + r")(?![\wА-Яа-яЁё])\s+до\s+\d",
)


@rule(
    id="unit-in-range",
    standards={GR2105: "6.16.5"},
    severity=Severity.WARNING,
    title="Единица величины повторена при обеих границах диапазона",
    allow_missing_suggestion=True,
)
def unit_in_range(doc: Document) -> Iterable[Finding]:
    """Ищет диапазон вида «от … до …», у первой границы которого стоит единица.
    Диапазон, записанный тире, правило не разбирает: тире между числами читается
    и как диапазон, и как вычитание.

    ## Почему это нарушение

    Обозначение единицы указывают после последнего числового значения диапазона:
    «от 1 до 5 мм». Повтор у первой границы ничего не уточняет, а запись удлиняет.

    ## Как исправить

    Убрать единицу у первой границы: «от 1 до 5 мм», «от минус 40 до плюс 10 °C».
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _RANGE.finditer(prose(doc, line)):
            unit = match.group("unit")
            yield unit_in_range.finding(
                doc,
                line,
                message=f"Единица «{unit}» указана и у первой границы диапазона.",
                requirement=(
                    "Обозначение единицы величины указывают после последнего "
                    "числового значения диапазона."
                ),
                col=match.start() + 1,
            )
