"""Иллюстрация, размещённая выше первой ссылки на неё."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import FIGURE_ENVIRONMENTS, float_position


@rule(
    id="figure-position",
    standards={G732: "6.5.1", GR2105: "6.9.1"},
    severity=Severity.ERROR,
    title="Иллюстрация размещена выше первой ссылки на неё",
    deprecated_ids=("G732-6.5.1-figure-position",),
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
    return float_position(
        figure_position,
        doc,
        FIGURE_ENVIRONMENTS,
        message=lambda key, where: (
            f"Рисунок с меткой {key!r} стоит выше первой ссылки на него ({where})."
        ),
        requirement=(
            "Иллюстрацию помещают непосредственно после текста, где она упомянута "
            "впервые, или на следующей странице."
        ),
    )
