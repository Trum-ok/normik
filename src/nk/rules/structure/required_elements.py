"""Наличие обязательных структурных элементов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import (
    ABSTRACT,
    BIBLIOGRAPHY,
    BIBLIOGRAPHY_ROLE,
    CONCLUSION,
    CONTENTS,
    CONTENTS_ROLE,
    INTRODUCTION,
    normalize_element,
)
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    BIBLIOGRAPHY_ENVIRONMENT,
    BIBTEX_COMMANDS,
    CONTENTS_COMMAND,
    is_full_document,
    structural_headings,
)


def _element(doc: Document, name: object) -> str:
    """Наименование из профиля в том виде, в каком его знает документ.

    Синоним кафедры разворачивается в каноническое наименование; наименование,
    которого словарь не знает, остаётся как есть и даёт находку об отсутствии —
    опечатка в профиле заметна, а не выключает проверку.
    """
    normalized = normalize_element(str(name))
    return doc.profile.elements.aliases.get(normalized, normalized)


#: Обязательные элементы, обнаружимые по исходникам. Титульный лист и основная
#: часть заголовка структурного элемента не имеют и сюда не входят.
REQUIRED = (
    ABSTRACT,
    CONTENTS,
    INTRODUCTION,
    CONCLUSION,
    BIBLIOGRAPHY,
)


@rule(
    id="G732-4-required-element-missing",
    clause="4",
    severity=Severity.ERROR,
    title="Отсутствует обязательный структурный элемент",
    params={"required": list(REQUIRED), "excluded": []},
)
def required_element_missing(doc: Document) -> Iterable[Finding]:
    """Проверяет наличие структурных элементов, обнаружимых по исходникам: реферата,
    содержания, введения, заключения и списка использованных источников. Содержание
    засчитывается и по команде его генерации, список источников — по окружению
    библиографии: заголовок ему во многих шаблонах печатает сам класс документа.
    Титульный лист и основная часть заголовка структурного элемента не имеют
    и не проверяются. Правило работает только на полном документе.

    Состав задаётся параметрами: `required` — весь перечень целиком, `excluded` —
    что выбросить из него, не переписывая остальное. Опечатка в наименовании
    оставляет лишнюю находку, а не отключает проверку молча.

    ## Почему это нарушение

    Перечисленные элементы обязательны: отчёт без любого из них неполон
    безотносительно к качеству остального текста.

    ## Как исправить

    Добавить недостающий элемент на положенное ему место — заголовком
    без номера, прописными буквами.
    """
    if not is_full_document(doc):
        return

    params = required_element_missing.params(doc)
    excluded = {_element(doc, item) for item in params["excluded"]}
    required = [
        name
        for name in (_element(doc, item) for item in params["required"])
        if name not in excluded
    ]

    elements = doc.profile.elements
    present = {element for _, element in structural_headings(doc)}
    if any(doc.structure.find_commands(CONTENTS_COMMAND)):
        present |= elements.role(CONTENTS_ROLE)
    if any(doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT)) or any(
        doc.structure.find_commands(*BIBTEX_COMMANDS)
    ):
        present |= elements.role(BIBLIOGRAPHY_ROLE)

    listed = ", ".join(name.lower() for name in required)
    requirement = f"Обязательные структурные элементы отчёта: {listed}."
    start = doc.structure.find_environments("document")
    anchor = next(iter(start))
    for element in required:
        if element in present:
            continue
        yield required_element_missing.finding(
            doc,
            anchor.span,
            message=f"В отчёте нет структурного элемента «{element}».",
            requirement=requirement,
            suggestion=f"Добавить \\section*{{{element}}} на положенное ему место.",
        )
