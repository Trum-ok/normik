"""Регистр заголовка структурного элемента."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_text, headings, structural_element, visible_text


@rule(
    id="G732-6.2.1-structural-heading-case",
    clause="6.2.1",
    severity=Severity.ERROR,
    title="Заголовок структурного элемента набран не прописными буквами",
    fixable=True,
)
def structural_heading_case(doc: Document) -> Iterable[Finding]:
    r"""Проверяет регистр заголовков структурных элементов — реферата, содержания,
    введения, заключения, списка использованных источников, приложений.

    ## Почему это нарушение

    Заголовки структурных элементов располагают посередине строки прописными
    буквами: так они отличаются от заголовков разделов основной части.

    ## Как исправить

    Записать заголовок прописными буквами в самом тексте. Команда оформления
    вроде `\MakeUppercase` меняет вид документа, но не исходник, и правило её
    не учитывает.
    """
    for command in headings(doc):
        text = heading_text(command)
        element = structural_element(text)
        if element is None:
            continue
        visible = visible_text(text)
        if visible == visible.upper():
            continue
        yield structural_heading_case.finding(
            doc,
            command.span,
            message=f"Заголовок структурного элемента «{visible}» набран не прописными буквами.",
            requirement=(
                "Заголовки структурных элементов располагают посередине строки "
                "прописными буквами, без точки в конце."
            ),
            suggestion=f"\\{command.name}{{{visible.upper()}}}",
            col=command.col,
            fix=command.region,
        )
