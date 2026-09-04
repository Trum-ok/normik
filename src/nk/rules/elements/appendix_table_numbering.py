"""Обозначение приложения в номере: таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import TABLE
from nk.core.rule import rule
from nk.rules._shared import appendix_numbering


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
    return appendix_numbering(
        appendix_table_numbering,
        doc,
        TABLE,
        "Таблицы каждого приложения обозначают отдельной нумерацией с добавлением перед цифрой обозначения приложения.",
    )
