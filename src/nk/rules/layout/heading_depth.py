"""Глубина рубрикации."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_level, heading_text, headings

#: Раздел, подраздел, пункт, подпункт — четыре уровня, как в примере 4.2.1.1.
DEFAULT_MAX_DEPTH = 4


@rule(
    id="G732-6.4.5-heading-depth",
    clause="6.4.5",
    severity=Severity.WARNING,
    title="Глубина рубрикации превышает четыре уровня",
    params={"max_depth": DEFAULT_MAX_DEPTH},
)
def heading_depth(doc: Document) -> Iterable[Finding]:
    """Считает уровень рубрики по команде заголовка и сравнивает с предельным.

    ## Почему это нарушение

    Рубрикация доходит до подпункта включительно — номер вида 4.2.1.1. Более
    глубокое дробление даёт номера, которые невозможно удержать при чтении.

    ## Как исправить

    Поднять рубрику на уровень выше либо оформить её перечислением внутри
    подпункта. Предел меняется параметром, если на кафедре принят другой.
    """
    max_depth = int(heading_depth.params(doc)["max_depth"])
    for command in headings(doc):
        depth = heading_level(doc, command)
        if depth <= max_depth:
            continue
        yield heading_depth.finding(
            doc,
            command.span,
            message=f"Заголовок «{heading_text(command)}» находится на {depth}-м уровне рубрикации.",
            requirement=(
                f"Рубрикация доходит до подпункта включительно — не более {max_depth} уровней "
                "вида 4.2.1.1."
            ),
            suggestion="Поднять рубрику на уровень выше либо оформить её перечислением.",
            col=command.col,
        )
