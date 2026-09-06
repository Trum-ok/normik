"""Порядок следования структурных элементов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import Elements
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import is_full_document, structural_headings


def _established_order(elements: Elements) -> str:
    """Порядок словами: взаимозаменяемые элементы перечисляются через «либо»."""
    places = (" либо ".join(name.lower() for name in place) for place in elements.ordered())
    return ", ".join(places)


@rule(
    id="elements-order",
    standards={G732: "4"},
    severity=Severity.ERROR,
    title="Структурные элементы идут не в установленном порядке",
    deprecated_ids=("G732-4-elements-order",),
)
def elements_order(doc: Document) -> Iterable[Finding]:
    """Сверяет порядок заголовков структурных элементов с установленным. Находка
    выдаётся на элемент, который стоит раньше положенного ему места. Правило
    работает только на полном документе.

    Порядок берётся из словаря элементов профиля, поэтому находка называет тот
    порядок, по которому проверяется этот отчёт, а не порядок по умолчанию.

    ## Почему это нарушение

    Порядок структурных элементов задан стандартом: список исполнителей, реферат,
    содержание, термины и определения, перечень сокращений и обозначений, введение,
    основная часть, заключение, список использованных источников, приложения.

    ## Как исправить

    Переставить элемент на положенное ему место. Порядок задаётся порядком
    включения файлов, а не оформлением заголовков.
    """
    if not is_full_document(doc):
        return

    elements = doc.profile.elements
    requirement = f"Структурные элементы следуют в порядке: {_established_order(elements)}."
    previous_name = ""
    previous_rank = 0
    for command, element in structural_headings(doc):
        rank = elements.rank(element)
        if rank >= previous_rank:
            previous_name, previous_rank = element, rank
            continue
        yield elements_order.finding(
            doc,
            command.span,
            message=f"Элемент «{element}» стоит после «{previous_name}».",
            requirement=requirement,
            suggestion=f"Переставить «{element}» выше «{previous_name}».",
            col=command.col,
        )
        previous_name, previous_rank = element, rank
