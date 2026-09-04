"""Наличие обязательных структурных элементов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import CONTENTS_COMMAND, is_full_document, structural_headings

#: Обязательные элементы, обнаружимые по исходникам. Титульный лист и основная
#: часть заголовка структурного элемента не имеют и сюда не входят.
REQUIRED = (
    "РЕФЕРАТ",
    "СОДЕРЖАНИЕ",
    "ВВЕДЕНИЕ",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
)


@rule(
    id="G732-4-required-element-missing",
    clause="4",
    severity=Severity.ERROR,
    title="Отсутствует обязательный структурный элемент",
)
def required_element_missing(doc: Document) -> Iterable[Finding]:
    """Проверяет наличие структурных элементов, обнаружимых по исходникам: реферата,
    содержания, введения, заключения и списка использованных источников. Содержание
    засчитывается и по команде его генерации. Титульный лист и основная часть
    заголовка структурного элемента не имеют и не проверяются. Правило работает
    только на полном документе.

    ## Почему это нарушение

    Перечисленные элементы обязательны: отчёт без любого из них неполон
    безотносительно к качеству остального текста.

    ## Как исправить

    Добавить недостающий элемент на положенное ему место — заголовком
    без номера, прописными буквами.
    """
    if not is_full_document(doc):
        return

    present = {element for _, element in structural_headings(doc)}
    if any(doc.structure.find_commands(CONTENTS_COMMAND)):
        present.add("СОДЕРЖАНИЕ")

    start = doc.structure.find_environments("document")
    anchor = next(iter(start))
    for element in REQUIRED:
        if element in present:
            continue
        yield required_element_missing.finding(
            doc,
            anchor.span,
            message=f"В отчёте нет структурного элемента «{element}».",
            requirement=(
                "Обязательные структурные элементы отчёта: титульный лист, реферат, "
                "содержание, введение, основная часть, заключение, "
                "список использованных источников."
            ),
            suggestion=f"Добавить \\section*{{{element}}} на положенное ему место.",
        )
