"""Таблица, размещённая выше первой ссылки на неё."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import TABLE_ENVIRONMENTS, float_position


@rule(
    id="table-position",
    standards={G732: "6.6.2", GR2105: "6.8.6"},
    severity=Severity.ERROR,
    title="Таблица размещена выше первой ссылки на неё",
    deprecated_ids=("G732-6.6.2-table-position",),
)
def table_position(doc: Document) -> Iterable[Finding]:
    r"""Сопоставляет положение таблицы с положением первой ссылки на неё. Находка
    выдаётся, когда таблица целиком стоит выше этой ссылки. Ссылки внутри самого
    окружения не учитываются, таблицу без ссылок разбирает отдельное правило.

    ## Почему это нарушение

    Таблицу помещают сразу после того текста, где она упомянута впервые, или
    на следующей странице: читатель встречает таблицу, уже зная, что в ней
    искать. Таблица, стоящая раньше упоминания, разрывает изложение.

    ## Как исправить

    Перенести окружение `table` ниже абзаца с первой ссылкой либо сослаться
    на таблицу раньше — там, где она по смыслу требуется.
    """
    return float_position(
        table_position,
        doc,
        TABLE_ENVIRONMENTS,
        message=lambda key, where: (
            f"Таблица с меткой {key!r} стоит выше первой ссылки на неё ({where})."
        ),
        requirement=(
            "Таблицу помещают непосредственно после текста, где она упомянута "
            "впервые, или на следующей странице."
        ),
    )
