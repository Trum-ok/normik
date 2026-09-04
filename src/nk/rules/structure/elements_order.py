"""Порядок следования структурных элементов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import ELEMENT_ORDER, is_full_document, structural_headings


@rule(
    id="G732-4-elements-order",
    clause="4",
    severity=Severity.ERROR,
    title="Структурные элементы идут не в установленном порядке",
)
def elements_order(doc: Document) -> Iterable[Finding]:
    """Сверяет порядок заголовков структурных элементов с установленным. Находка
    выдаётся на элемент, который стоит раньше положенного ему места. Правило
    работает только на полном документе.

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

    previous_name = ""
    previous_rank = 0
    for command, element in structural_headings(doc):
        rank = ELEMENT_ORDER[element]
        if rank >= previous_rank:
            previous_name, previous_rank = element, rank
            continue
        yield elements_order.finding(
            doc,
            command.span,
            message=f"Элемент «{element}» стоит после «{previous_name}».",
            requirement=(
                "Структурные элементы следуют в порядке: список исполнителей, реферат, "
                "содержание, термины и определения, перечень сокращений и обозначений, "
                "введение, основная часть, заключение, список использованных источников, "
                "приложения."
            ),
            suggestion=f"Переставить «{element}» выше «{previous_name}».",
            col=command.col,
        )
        previous_name, previous_rank = element, rank
