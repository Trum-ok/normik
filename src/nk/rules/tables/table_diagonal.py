"""Диагональная линия в шапке таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732

#: Команды пакетов, рисующие диагональ в ячейке шапки.
DIAGONAL_COMMANDS = frozenset({"diagbox", "backslashbox", "slashbox"})


@rule(
    id="G732-6.6.6-table-diagonal",
    standards={G732: "6.6.6"},
    severity=Severity.ERROR,
    title="Шапка таблицы разделена диагональной линией",
)
def table_diagonal(doc: Document) -> Iterable[Finding]:
    r"""Ищет команды, которые делят ячейку шапки диагональю: `\diagbox`,
    `\backslashbox` и `\slashbox`. Диагональ, нарисованную средствами графики
    поверх таблицы, по исходникам опознать нельзя.

    ## Почему это нарушение

    Разделять заголовки граф и строк диагональными линиями не допускается:
    в такой ячейке непонятно, к какой оси относится каждая её половина.

    ## Как исправить

    Вынести заголовок строк в отдельную первую графу, а в шапке оставить
    заголовки граф.
    """
    for command in doc.structure.find_commands(*DIAGONAL_COMMANDS):
        yield table_diagonal.finding(
            doc,
            command.span,
            message=f"Ячейка шапки разделена диагональю командой \\{command.name}.",
            requirement=(
                "Разделять заголовки граф и строк таблицы диагональными линиями не допускается."
            ),
            suggestion=(
                f"Убрать \\{command.name}: заголовок строк вынести в отдельную первую графу."
            ),
            col=command.col,
        )
