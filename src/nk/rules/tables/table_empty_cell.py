"""Пустая графа в таблице."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import DASH, TABLE_BODY_ENVIRONMENTS, table_rows, visible_text


@rule(
    id="table-empty-cell",
    standards={GR2105: "6.8.19"},
    severity=Severity.WARNING,
    title="Графа таблицы оставлена пустой",
)
def table_empty_cell(doc: Document) -> Iterable[Finding]:
    r"""Ищет графы без содержимого. Строка с `\multicolumn` или `\multirow`
    пропускается: объединённая ячейка оставляет пустые графы по построению,
    и отличить их от забытых по исходнику нельзя.

    ## Почему это нарушение

    Пустая графа читается двояко: то ли данных нет, то ли их забыли внести.
    Прочерк говорит, что данных нет, и снимает вопрос.

    ## Как исправить

    Поставить в пустую графу тире.
    """
    for environment in doc.structure.find_environments(*TABLE_BODY_ENVIRONMENTS):
        for row in table_rows(doc, environment):
            if row.spanning:
                continue
            empty = [number for number, cell in enumerate(row.cells, 1) if not visible_text(cell)]
            if not empty:
                continue
            listed = ", ".join(str(number) for number in empty)
            noun = "графа" if len(empty) == 1 else "графы"
            yield table_empty_cell.finding(
                doc,
                doc.lines_of(environment.path)[row.lineno - 1],
                message=f"В строке таблицы пуста {noun} {listed}.",
                requirement="При отсутствии данных в графе таблицы ставят прочерк.",
                suggestion=f"Поставить в пустую графу тире: {DASH}",
            )
