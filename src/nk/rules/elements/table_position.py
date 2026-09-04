"""Таблица, размещённая выше первой ссылки на неё."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    TABLE_ENVIRONMENTS,
    first_outside_reference,
    is_below,
    labels,
    place,
)


@rule(
    id="G732-6.6.2-table-position",
    clause="6.6.2",
    severity=Severity.ERROR,
    title="Таблица размещена выше первой ссылки на неё",
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
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            continue
        reference = first_outside_reference(doc, environment, keys)
        if reference is None or not is_below(doc, reference, environment.span):
            continue
        yield table_position.finding(
            doc,
            environment.span,
            message=(
                f"Таблица с меткой {keys[0]!r} стоит выше первой ссылки на неё "
                f"({place(reference, environment.span)})."
            ),
            requirement=(
                "Таблицу помещают непосредственно после текста, где она упомянута "
                "впервые, или на следующей странице."
            ),
            suggestion=(
                f"Перенести окружение {environment.name} ниже абзаца со ссылкой "
                f"(строка {reference.lineno})."
            ),
        )
