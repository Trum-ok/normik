"""Разрывный пробел перед номером в ссылке."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import NBSP
from nk.rules._text import gaps

#: «рисунке 1», «таблице \ref{...}», «формуле (1)», «приложении А»
BEFORE_NUMBER = re.compile(
    r"(?:[Рр]исун\w+|[Тт]аблиц\w+|[Фф]ормул\w+|[Пп]риложени\w+)"
    r"( +)(?=[\d(]|[А-Я]\b|\\(?:ref|eqref|autoref))"
)


@rule(
    id="NK-STYLE-reference-nbsp",
    clause="",
    severity=Severity.INFO,
    title="Номер в ссылке отделён разрывным пробелом",
    fixable=True,
)
def reference_nbsp(doc: Document) -> Iterable[Finding]:
    """Находит обычный пробел между словом и номером в ссылке.

    ## Почему это замечание

    Обычный пробел позволяет перенести номер на следующую строку, оставив
    «рисунке» в конце предыдущей. ГОСТ 7.32-2017 этого не регулирует, но в
    вёрстке отчёта такой разрыв выглядит ошибкой.

    ## Как исправить

    Поставить неразрывный пробел `~`: `на рисунке~\\ref{fig:setup}`.
    """
    for gap in gaps(doc, BEFORE_NUMBER):
        yield reference_nbsp.finding(
            doc,
            gap.line,
            message="Между словом и номером стоит обычный пробел.",
            requirement="Номер в ссылке привязывают к слову неразрывным пробелом.",
            suggestion=f"Поставить неразрывный пробел: {NBSP}",
            col=gap.col,
            fix=gap.fix,
        )
