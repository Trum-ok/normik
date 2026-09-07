"""Точка в конце библиографического описания."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import GR70100
from nk.rules._bibliography import entries


@rule(
    id="bibitem-final-dot",
    standards={GR70100: "4.6.1"},
    severity=Severity.ERROR,
    title="Библиографическое описание не заканчивается точкой",
    fixable=True,
)
def bibitem_final_dot(doc: Document) -> Iterable[Finding]:
    r"""Проверяет, что описание источника закрыто точкой. Записи разбираются
    только в списке, набранном в исходнике: у списка, собираемого BibTeX,
    описаний в `.tex` нет.

    ## Почему это нарушение

    Точка в конце — предписанный знак, а не грамматический: он закрывает
    описание целиком и отделяет его от следующего. Без него две соседние
    записи в наборе сливаются в одну.

    ## Как исправить

    Поставить точку после последнего элемента описания: `... — 250 с.`
    """
    for entry in entries(doc):
        tail = entry.tail
        if tail is None or entry.text.rstrip().endswith("."):
            continue
        line, col = tail
        yield bibitem_final_dot.finding(
            doc,
            line,
            message=f"Описание источника {entry.key!r} не заканчивается точкой.",
            requirement="В конце библиографического описания ставят точку.",
            suggestion="Поставить точку в конце описания.",
            col=col,
            fix=Fix(Region.at(line.path, line.lineno, col), "."),
        )
