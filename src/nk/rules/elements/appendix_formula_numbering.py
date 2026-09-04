"""Обозначение приложения в номере: формулы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import EQUATION, Scheme
from nk.core.rule import rule


@rule(
    id="G732-6.8.5-appendix-numbering",
    clause="6.8.5",
    severity=Severity.ERROR,
    title="Формула приложения нумеруется без обозначения приложения",
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
    for item in doc.numbering.by_kind(EQUATION):
        if not item.in_appendix or item.scheme is Scheme.BY_SECTION:
            continue
        yield appendix_formula_numbering.finding(
            doc,
            item.span,
            message=(
                f"{item.title} находится в приложении {item.appendix}, "
                f"но нумеруется сквозной нумерацией основной части."
            ),
            requirement="Формулы каждого приложения нумеруют отдельно, добавляя перед цифрой обозначение приложения.",
            suggestion=(
                "Добавить в преамбулу \\counterwithin{equation}{section}: "
                f"тогда номер станет {item.appendix}.1 и далее."
            ),
        )
