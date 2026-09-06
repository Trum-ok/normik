"""Число ключевых слов в реферате."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import keyword_lists

DEFAULT_MIN = 5
DEFAULT_MAX = 15


@rule(
    id="keywords-count",
    standards={G732: "5.3.2.1"},
    severity=Severity.ERROR,
    title="Число ключевых слов вне допустимого диапазона",
    params={"keywords_min": DEFAULT_MIN, "keywords_max": DEFAULT_MAX},
    deprecated_ids=("G732-5.3.2.1-keywords-count",),
)
def keywords_count(doc: Document) -> Iterable[Finding]:
    """Считает элементы перечня ключевых слов в реферате и сравнивает с допустимым
    диапазоном. Разделитель — запятая.

    ## Почему это нарушение

    Перечень ключевых слов служит для поиска отчёта: слишком короткий не описывает
    работу, слишком длинный перестаёт выделять главное.

    ## Как исправить

    Довести перечень до допустимого числа слов и словосочетаний, взятых из текста
    отчёта. Границы меняются профилем, если на кафедре принят другой диапазон.
    """
    params = keywords_count.params(doc)
    lower = int(params["keywords_min"])
    upper = int(params["keywords_max"])

    for entry in keyword_lists(doc):
        count = len(entry.words)
        if lower <= count <= upper:
            continue
        side = "меньше" if count < lower else "больше"
        yield keywords_count.finding(
            doc,
            entry.line,
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
