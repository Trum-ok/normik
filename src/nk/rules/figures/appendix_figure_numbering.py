"""Обозначение приложения в номере: иллюстрации."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import FIGURE
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import appendix_numbering


@rule(
    id="G732-6.5.5-appendix-numbering",
    standards={G732: "6.5.5"},
    severity=Severity.ERROR,
    title="Иллюстрация приложения нумеруется без его обозначения",
)
def appendix_figure_numbering(doc: Document) -> Iterable[Finding]:
    """Проверяет, что иллюстрации внутри приложения нумеруются с его обозначением.

    ## Почему это нарушение

    Нумерация в приложении отдельная: она начинается заново и несёт обозначение
    самого приложения. Сквозной номер из основной части ссылку «рисунок А.1»
    сделать не позволяет.

    ## Как исправить

    Задать схему нумерации в пределах раздела — тогда внутри приложения номер
    складывается из его буквы и порядкового номера.
    """
    return appendix_numbering(
        appendix_figure_numbering,
        doc,
        FIGURE,
        "Иллюстрации каждого приложения обозначают отдельной нумерацией с добавлением перед цифрой обозначения приложения.",
    )
