"""Подсписок внутри маркированного списка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import LIST_ENVIRONMENTS, MARKED_LIST_ENVIRONMENTS


@rule(
    id="enumeration-marker-nested",
    standards={GR2105: "6.7.4"},
    severity=Severity.ERROR,
    title="Элемент маркированного списка разбит на подсписок",
    allow_missing_suggestion=True,
)
def enumeration_marker_nested(doc: Document) -> Iterable[Finding]:
    r"""Ищет список, вложенный непосредственно в маркированный. Находка выдаётся
    на вложенный список: именно он показывает, что верхний уровень пора
    обозначить.

    ## Почему это нарушение

    Уровни списка различают по обозначению элемента. Маркер обозначения не
    даёт, поэтому при разбиении на подсписок верхний уровень перестаёт
    читаться: непонятно, к какому элементу относится вложенный список.

    ## Как исправить

    Обозначить элементы верхнего уровня буквами или номерами со скобкой —
    в LaTeX заменить внешний `itemize` на `enumerate`.
    """
    for environment in doc.structure.find_environments(*MARKED_LIST_ENVIRONMENTS):
        for child in environment.children:
            if child.name not in LIST_ENVIRONMENTS:
                continue
            yield enumeration_marker_nested.finding(
                doc,
                child.span,
                message="Подсписок вложен в маркированный список.",
                requirement=(
                    "Маркированный список не применяют, если перечисление "
                    "подразделяется на другой список перечислений."
                ),
            )
