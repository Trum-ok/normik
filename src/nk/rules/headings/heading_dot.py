"""Точка в конце заголовка рубрики."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import heading_text, headings, one_line


@rule(
    id="heading-dot",
    standards={G732: "6.2.3", GR2105: "6.6.2"},
    severity=Severity.ERROR,
    title="Заголовок заканчивается точкой",
    fixable=True,
    deprecated_ids=("G732-6.2.3-heading-dot",),
)
def heading_dot(doc: Document) -> Iterable[Finding]:
    """Проверяет заголовки разделов, подразделов и структурных элементов на точку
    в конце.

    ## Почему это нарушение

    Заголовок — не предложение: точка в конце не ставится ни у структурных
    элементов, ни у рубрик основной части.

    ## Как исправить

    Убрать точку. Знаки внутри заголовка — двоеточие, запятая — нарушением
    не являются.
    """
    for command in headings(doc):
        text = heading_text(command)
        if not text.endswith("."):
            continue
        yield heading_dot.finding(
            doc,
            command.span,
            message="Заголовок заканчивается точкой.",
            requirement=(
                "Заголовки разделов, подразделов и структурных элементов "
                "печатают без точки в конце."
            ),
            suggestion=f"\\{command.name}{{{one_line(text.rstrip('.'))}}}",
            col=command.col,
            fix=command.region,
        )
