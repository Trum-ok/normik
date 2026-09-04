"""Смешение схем нумерации иллюстраций."""

from collections.abc import Iterable

from nk.core.document import Document, Span
from nk.core.finding import Finding, Severity
from nk.core.numbering import FIGURE
from nk.core.rule import rule


@rule(
    id="G732-6.5.4-numbering-scheme-mixed",
    clause="6.5.4",
    severity=Severity.ERROR,
    title="Схема нумерации иллюстраций задана в документе несколько раз",
)
def figure_numbering_scheme_mixed(doc: Document) -> Iterable[Finding]:
    """Проверяет, что схема нумерации иллюстраций объявлена один раз.

    ## Почему это нарушение

    Иллюстрации нумеруют либо сквозной нумерацией, либо в пределах раздела.
    Переопределение схемы посреди отчёта означает, что часть рисунков получит
    номера одного вида, а часть — другого, и ссылки перестанут быть однозначными.

    ## Как исправить

    Оставить одно объявление схемы в преамбуле и убрать остальные.
    """
    changes = doc.numbering.changes_of(FIGURE)
    first, *rest = changes if changes else (None,)
    if first is None:
        return
    for change in rest:
        yield figure_numbering_scheme_mixed.finding(
            doc,
            Span(change.path, change.lineno, change.lineno),
            message=(
                f"Схема нумерации иллюстраций переопределяется повторно: "
                f"было «{first.scheme.value}», стало «{change.scheme.value}»."
            ),
            requirement=(
                "Иллюстрации нумеруют либо сквозной нумерацией по всему отчёту, "
                "либо в пределах раздела — но одной схемой."
            ),
            suggestion="Оставить одно объявление схемы нумерации в преамбуле.",
            col=change.col,
        )
