"""Число ключевых слов в реферате."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import keyword_lists

DEFAULT_MIN = 5
DEFAULT_MAX = 15


@rule(
    id="G732-5.3.2.1-keywords-count",
    clause="5.3.2.1",
    severity=Severity.ERROR,
    title="Число ключевых слов вне допустимого диапазона",
    params={"keywords_min": DEFAULT_MIN, "keywords_max": DEFAULT_MAX},
)
def keywords_count(doc: Document) -> Iterable[Finding]:
    params = keywords_count.params(doc)
    lower = int(params["keywords_min"])
    upper = int(params["keywords_max"])

    for line, keywords in keyword_lists(doc):
        count = len(keywords)
        if lower <= count <= upper:
            continue
        side = "меньше" if count < lower else "больше"
        yield keywords_count.finding(
            doc,
            line,
            message=f"В перечне {count} ключевых слов — {side} допустимого.",
            requirement=(
                f"Перечень ключевых слов включает от {lower} до {upper} слов "
                "или словосочетаний из текста отчёта."
            ),
            suggestion=(
                f"Довести число ключевых слов до {lower}."
                if count < lower
                else f"Сократить перечень до {upper} слов."
            ),
        )
