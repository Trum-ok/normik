"""Иллюстрация, размещённая выше первой ссылки на неё."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    FIGURE_ENVIRONMENTS,
    first_outside_reference,
    is_below,
    labels,
    place,
)


@rule(
    id="G732-6.5.1-figure-position",
    clause="6.5.1",
    severity=Severity.ERROR,
    title="Иллюстрация размещена выше первой ссылки на неё",
)
def figure_position(doc: Document) -> Iterable[Finding]:
    r"""Сопоставляет положение рисунка с положением первой ссылки на него. Находка
    выдаётся, когда рисунок целиком стоит выше этой ссылки. Ссылки внутри самого
    окружения не учитываются, рисунок без ссылок разбирает отдельное правило.

    ## Почему это нарушение

    Иллюстрацию помещают сразу после того текста, где она упомянута впервые,
    или на следующей странице: читатель встречает рисунок, уже зная, зачем он
    здесь. Рисунок, стоящий раньше упоминания, разрывает изложение.

    ## Как исправить

    Перенести окружение `figure` ниже абзаца с первой ссылкой либо сослаться
    на рисунок раньше — там, где он по смыслу требуется.
    """
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            continue
        reference = first_outside_reference(doc, environment, keys)
        if reference is None or not is_below(doc, reference, environment.span):
            continue
        yield figure_position.finding(
            doc,
            environment.span,
            message=(
                f"Рисунок с меткой {keys[0]!r} стоит выше первой ссылки на него "
                f"({place(reference, environment.span)})."
            ),
            requirement=(
                "Иллюстрацию помещают непосредственно после текста, где она упомянута "
                "впервые, или на следующей странице."
            ),
            suggestion=(
                f"Перенести окружение {environment.name} ниже абзаца со ссылкой "
                f"(строка {reference.lineno})."
            ),
        )
