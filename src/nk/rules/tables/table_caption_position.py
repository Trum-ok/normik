"""Наименование таблицы под самой таблицей."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import TABLE_ENVIRONMENTS, captions, first_tabular_line


@rule(
    id="table-caption-position",
    standards={G732: "6.6.3"},
    severity=Severity.ERROR,
    title="Наименование таблицы расположено ниже самой таблицы",
    deprecated_ids=("G732-6.6.3-caption-position",),
)
def table_caption_position(doc: Document) -> Iterable[Finding]:
    r"""Сравнивает положение `\caption` с началом самой таблицы внутри окружения.

    ## Почему это нарушение

    Наименование помещают над таблицей слева, без абзацного отступа: читающий
    должен понять, что перед ним, до того как начнёт разбирать головку.

    ## Как исправить

    Перенести `\caption` выше начала таблицы.
    """
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        tabular = first_tabular_line(environment)
        if tabular is None:
            continue
        for command in captions(environment):
            if command.lineno <= tabular:
                continue
            yield table_caption_position.finding(
                doc,
                command.span,
                message="Наименование таблицы стоит ниже самой таблицы.",
                requirement="Наименование помещают над таблицей слева, без абзацного отступа.",
                suggestion=f"Перенести \\{command.name} выше строки {tabular}, до начала таблицы.",
                col=command.col,
            )
