"""Нумерация заголовка структурного элемента."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import heading_text, headings, is_numbered, structural_element


@rule(
    id="structural-heading-numbered",
    standards={G732: "6.2.1"},
    severity=Severity.ERROR,
    title="Заголовок структурного элемента пронумерован",
    fixable=True,
    deprecated_ids=("G732-6.2.1-structural-heading-numbered",),
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
    в содержание вручную, если этого требует класс документа. Если заголовок набран
    макросом шаблона, правку вносят в объявление макроса, а не в текст отчёта.
    """
    for command in headings(doc):
        text = heading_text(command)
        element = structural_element(doc, text)
        if element is None or not is_numbered(doc, command):
            continue
        alias = doc.headings.alias_of(command.name)
        yield structural_heading_numbered.finding(
            doc,
            command.span,
            message=f"Заголовок структурного элемента «{element}» получает порядковый номер.",
            requirement=(
                "Заголовки структурных элементов не нумеруются: "
                "порядковые номера имеют только разделы основной части."
            ),
            suggestion=(
                f"Объявить \\{command.name} через ненумерованную \\{alias}*"
                if alias
                else f"\\{command.name}*{{{text}}}"
            ),
            col=command.col,
            fix=None if alias else command.region,
        )
