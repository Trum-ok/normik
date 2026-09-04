"""Обозначение приложения в номере: иллюстрации."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.numbering import FIGURE, Scheme
from nk.core.rule import rule


@rule(
    id="G732-6.5.5-appendix-numbering",
    clause="6.5.5",
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
    for item in doc.numbering.by_kind(FIGURE):
        if not item.in_appendix or item.scheme is Scheme.BY_SECTION:
            continue
        yield appendix_figure_numbering.finding(
            doc,
            item.span,
            message=(
                f"{item.title} находится в приложении {item.appendix}, "
                f"но нумеруется сквозной нумерацией основной части."
            ),
            requirement="Иллюстрации каждого приложения обозначают отдельной нумерацией с добавлением перед цифрой обозначения приложения.",
            suggestion=(
                "Добавить в преамбулу \\counterwithin{figure}{section}: "
                f"тогда номер станет {item.appendix}.1 и далее."
            ),
        )
