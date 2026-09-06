"""Надпись над продолжением таблицы."""

from collections.abc import Iterable

from nk.core.document import Document, Environment
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import visible_text

#: Окружение, которое само разбивает таблицу по страницам.
BREAKING_ENVIRONMENT = "longtable"

CONTINUATION = "продолжение таблицы"


@rule(
    id="table-continuation",
    standards={G732: "6.6.3"},
    severity=Severity.WARNING,
    title="Над продолжением таблицы нет надписи «Продолжение таблицы»",
    allow_missing_suggestion=True,
)
def table_continuation(doc: Document) -> Iterable[Finding]:
    r"""Проверяет `longtable` — окружение, которое разбивает таблицу по страницам
    само, — на надпись «Продолжение таблицы» в её исходнике.

    Таблицу, разбитую вручную на несколько `table`, правило не проверяет: по
    исходникам перенос от двух самостоятельных таблиц не отличить. По той же
    причине не проверяется обычная `tabular`: разобьётся она или нет, известно
    только после вёрстки.

    ГОСТ Р 2.105 надпись при подготовке документа программными средствами не
    требует (п. 6.8.7), поэтому под ним правило не запускается.

    ## Почему это нарушение

    Наименование таблицы стоит только над первой её частью. Читающий, открыв
    следующую страницу, видит головку без наименования и не знает, что перед
    ним продолжение и какой именно таблицы.

    ## Как исправить

    Объявить в `longtable` строку продолжения:
    `\multicolumn{N}{l}{Продолжение таблицы \thetable} \\ \endhead`.
    """
    for environment in doc.structure.find_environments(BREAKING_ENVIRONMENT):
        if CONTINUATION in _body(doc, environment).casefold():
            continue
        yield table_continuation.finding(
            doc,
            environment.span,
            message="Таблица разбивается по страницам, а надписи «Продолжение таблицы» нет.",
            requirement=(
                "Над частями таблицы, перенесёнными на другие страницы, слева пишут "
                "слова «Продолжение таблицы» с её номером."
            ),
        )


def _body(doc: Document, environment: Environment) -> str:
    lines = doc.lines_of(environment.path)[environment.span.start : environment.span.end - 1]
    return " ".join(visible_text(line.stripped) for line in lines)
