"""Точка в конце перечня ключевых слов."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import KeywordList, keyword_lists

#: Точка в самом конце перечня: за ней остаются лишь пробелы и закрывающие скобки.
FINAL_DOT = re.compile(r"\.(?=[\s}]*$)")


@rule(
    id="G732-6.12.2-keywords-final-dot",
    standards={G732: "6.12.2"},
    severity=Severity.ERROR,
    title="Перечень ключевых слов заканчивается точкой",
    fixable=True,
)
def keywords_final_dot(doc: Document) -> Iterable[Finding]:
    """Проверяет последний элемент перечня ключевых слов на точку в конце.

    ## Почему это нарушение

    Перечень ключевых слов — не предложение: слова идут в строку через запятые,
    и точка в конце не ставится.

    ## Как исправить

    Убрать точку после последнего ключевого слова.
    """
    for entry in keyword_lists(doc):
        if not entry.words or not entry.words[-1].endswith("."):
            continue
        yield keywords_final_dot.finding(
            doc,
            entry.line,
            message="Перечень ключевых слов заканчивается точкой.",
            requirement="Перечень ключевых слов приводят без точки в конце.",
            suggestion=f"Убрать точку после «{entry.words[-1][:-1]}».",
            fix=_removal(entry),
        )


def _removal(entry: KeywordList) -> Fix | None:
    """Правка убирает один символ, поэтому заменой текста подсказки не выражается."""
    last = entry.lines[-1]
    match = FINAL_DOT.search(last.stripped)
    if match is None:
        return None
    col = match.start() + 1
    return Fix(Region.in_line(last.path, last.lineno, col, col + 1), "")
