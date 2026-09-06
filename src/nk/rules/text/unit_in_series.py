"""Единица величины при каждом значении ряда."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._text import PHYSICAL_UNITS, is_code, prose

_UNIT = "(?:" + "|".join(sorted(PHYSICAL_UNITS, key=len, reverse=True)) + ")"

#: Два значения подряд, у каждого своя единица: «1,50 м; 1,75 м».
_REPEATED = re.compile(
    r"\d[\d,.]*\s*~?\s*(?P<unit>" + _UNIT + r")(?![\wА-Яа-яЁё])"
    r"\s*[;,]\s*"
    r"\d[\d,.]*\s*~?\s*(?P=unit)(?![\wА-Яа-яЁё])"
)


@rule(
    id="unit-in-series",
    standards={GR2105: "6.16.4"},
    severity=Severity.WARNING,
    title="Единица величины повторена при каждом значении ряда",
    allow_missing_suggestion=True,
)
def unit_in_series(doc: Document) -> Iterable[Finding]:
    """Ищет два соседних значения одной и той же единицы, разделённых запятой или
    точкой с запятой. Значения с разными единицами рядом нарушением не являются:
    ряда они не образуют.

    ## Почему это нарушение

    Если ряд значений выражен в одной единице, её указывают только после
    последнего значения: повтор при каждом числе удлиняет запись, ничего
    к ней не добавляя.

    ## Как исправить

    Убрать единицу у всех значений ряда, кроме последнего: «1,50; 1,75; 2,00 м».
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _REPEATED.finditer(prose(doc, line)):
            unit = match.group("unit")
            yield unit_in_series.finding(
                doc,
                line,
                message=f"Единица «{unit}» повторена при каждом значении ряда.",
                requirement=("Единицу величины указывают только после последнего значения ряда."),
                col=match.start() + 1,
            )
