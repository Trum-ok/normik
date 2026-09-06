"""Число, оторванное от единицы измерения."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105, Origin
from nk.rules._shared import NBSP
from nk.rules._text import gaps

#: Сокращения со точкой: сведения об объёме реферата, даты, счётные единицы.
ABBREVIATIONS = "с. кн. рис. табл. ил. источн. прил. шт. экз. руб. тыс. г. гг. в. мин. ч. сут."

#: Единицы физических величин и знаки. Процент — только экранированный: голый
#: «%» LaTeX считает началом комментария, и до правила он не доходит.
UNITS = (
    "мкм нм мм см дм км м мг кг г т мл л "
    "мин ч сут Гц кГц МГц ГГц Вт кВт мВт кВ мВ В мА А кОм Ом "
    "кДж МДж Дж кПа МПа Па кН Н К \\% ‰ °C °К"
)

#: Одиночное «с» без точки не берём: «таблица 2 с результатами» от «2 с»
#: (секунды) по тексту не отличить.
_TOKENS = sorted((ABBREVIATIONS + " " + UNITS).split(), key=len, reverse=True)
_BEFORE_UNIT = re.compile(
    r"\d( )(?=(?:" + "|".join(re.escape(token) for token in _TOKENS) + r")(?![\wА-Яа-яЁё]))"
)


@rule(
    id="unit-nbsp",
    standards={GR2105: "6.16.6"},
    origin=Origin.UNIVERSAL,
    severity=Severity.INFO,
    title="Число не привязано к единице измерения",
    fixable=True,
    deprecated_ids=("NK-STYLE-unit-nbsp",),
)
def unit_nbsp(doc: Document) -> Iterable[Finding]:
    """Находит обычный пробел между числом и следующей за ним единицей или сокращением.

    ## Почему это замечание

    Перенос, оставляющий число в конце строки, а единицу в начале следующей,
    читается как ошибка набора. Особенно заметно в сведениях об объёме отчёта,
    где чисел и сокращений много подряд.

    ## Как исправить

    Поставить неразрывный пробел: `45~с.`, `12~%`, `5~мм`.

    Одиночное «с» без точки правило не проверяет: «таблица 2 с результатами»
    от секунд по тексту не отличить.
    """
    for gap in gaps(doc, _BEFORE_UNIT):
        yield unit_nbsp.finding(
            doc,
            gap.line,
            message="Между числом и единицей стоит обычный пробел.",
            requirement="Число и следующую за ним единицу связывают неразрывным пробелом.",
            suggestion=f"Поставить неразрывный пробел: {NBSP}",
            col=gap.col,
            fix=gap.fix,
        )
