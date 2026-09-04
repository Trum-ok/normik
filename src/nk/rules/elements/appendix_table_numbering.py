"""Обозначение приложения в номере: таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import TABLE, Scheme
from nk.core.rule import rule


@rule(
    id="G732-6.6.4-appendix-numbering",
    clause="6.6.4",
    severity=Severity.ERROR,
    title="Таблица приложения нумеруется без его обозначения",
)
def appendix_table_numbering(doc: Document) -> Iterable[Finding]:
    """Проверяет, что таблицы внутри приложения нумеруются с его обозначением.

    ## Почему это нарушение

    Нумерация в приложении отдельная: она начинается заново и несёт обозначение
    самого приложения. Сквозной номер из основной части ссылку «таблица А.1»
    сделать не позволяет.

    ## Как исправить

    Задать схему нумерации в пределах раздела — тогда внутри приложения номер
    складывается из его буквы и порядкового номера.
    """
    for item in doc.numbering.by_kind(TABLE):
        if not item.in_appendix or item.scheme is Scheme.BY_SECTION:
            continue
        yield appendix_table_numbering.finding(
            doc,
            item.span,
            message=(
                f"{item.title} находится в приложении {item.appendix}, "
                f"но нумеруется сквозной нумерацией основной части."
            ),
            requirement="Таблицы каждого приложения обозначают отдельной нумерацией с добавлением перед цифрой обозначения приложения.",
            suggestion=(
                "Добавить в преамбулу \\counterwithin{table}{section}: "
                f"тогда номер станет {item.appendix}.1 и далее."
            ),
        )
