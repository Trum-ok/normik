"""Размер таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import TABLE_BODY_ENVIRONMENTS, table_rows

#: Наименьшее число граф и строк.
MINIMUM = 2


@rule(
    id="table-too-small",
    standards={GR2105: "6.8.1"},
    severity=Severity.ERROR,
    title="В таблице меньше двух граф или двух строк",
    allow_missing_suggestion=True,
)
def table_too_small(doc: Document) -> Iterable[Finding]:
    r"""Считает строки и графы по исходнику: строки разделены `\\`, графы — `&`.
    Строки из одних линеек не в счёт. Таблица с объединёнными ячейками
    пропускается: `\multicolumn` меняет число граф в строке, и посчитать их
    по исходнику нельзя.

    ## Почему это нарушение

    Таблицу применяют для сравнения показателей, а сравнивать нечего, если
    графа или строка одна: такие данные излагают текстом.

    ## Как исправить

    Дописать недостающие графы или строки либо развернуть таблицу в текст.
    """
    for environment in doc.structure.find_environments(*TABLE_BODY_ENVIRONMENTS):
        rows = table_rows(doc, environment)
        if not rows or any(row.spanning for row in rows):
            continue
        columns = max(len(row.cells) for row in rows)
        lacking = _lacking(len(rows), columns)
        if lacking is None:
            continue
        yield table_too_small.finding(
            doc,
            environment.span,
            message=f"В таблице {lacking}.",
            requirement="Таблица должна содержать не менее двух граф и не менее двух строк.",
        )


def _lacking(rows: int, columns: int) -> str | None:
    """Чего в таблице не хватает, словами, либо ``None``, если хватает всего."""
    missing = []
    if columns < MINIMUM:
        missing.append(f"{columns} графа")
    if rows < MINIMUM:
        missing.append(f"{rows} строка")
    return " и ".join(missing) if missing else None
