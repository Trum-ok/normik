"""Обозначение приложения в номере: формулы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import EQUATION
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import appendix_numbering


@rule(
    id="formula-appendix-numbering",
    standards={G732: "6.8.5"},
    severity=Severity.ERROR,
    title="Формула приложения нумеруется без обозначения приложения",
    deprecated_ids=("G732-6.8.5-appendix-numbering",),
)
def appendix_formula_numbering(doc: Document) -> Iterable[Finding]:
    """Проверяет, что формулы внутри приложения нумеруются с его обозначением.

    ## Почему это нарушение

    Нумерация в приложении отдельная: она начинается заново и несёт обозначение
    самого приложения. Сквозной номер из основной части ссылку «формула А.1»
    сделать не позволяет.

    ## Как исправить

    Задать схему нумерации в пределах раздела — тогда внутри приложения номер
    складывается из его буквы и порядкового номера.
    """
    return appendix_numbering(
        appendix_formula_numbering,
        doc,
        EQUATION,
        "Формулы каждого приложения нумеруют отдельно, добавляя перед цифрой обозначение приложения.",
    )
