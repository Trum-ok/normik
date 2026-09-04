"""Нумерация заголовка структурного элемента."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_text, headings, is_numbered, structural_element


@rule(
    id="G732-6.2.1-structural-heading-numbered",
    clause="6.2.1",
    severity=Severity.ERROR,
    title="Заголовок структурного элемента пронумерован",
    fixable=True,
)
def structural_heading_numbered(doc: Document) -> Iterable[Finding]:
    """Ищет заголовки структурных элементов, заданные нумерованной формой команды
    раздела.

    ## Почему это нарушение

    Порядковые номера имеют только разделы основной части. Пронумерованное
    введение сдвигает нумерацию всех последующих разделов и попадает в содержание
    как раздел 1.

    ## Как исправить

    Использовать ненумерованную форму команды — со звёздочкой — и добавить элемент
    в содержание вручную, если этого требует класс документа.
    """
    for command in headings(doc):
        text = heading_text(command)
        element = structural_element(text)
        if element is None or not is_numbered(command):
            continue
        yield structural_heading_numbered.finding(
            doc,
            command.span,
            message=f"Заголовок структурного элемента «{element}» получает порядковый номер.",
            requirement=(
                "Заголовки структурных элементов не нумеруются: "
                "порядковые номера имеют только разделы основной части."
            ),
            suggestion=f"\\{command.name}*{{{text}}}",
            col=command.col,
            fix=command.region,
        )
