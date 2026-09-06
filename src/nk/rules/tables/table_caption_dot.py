"""Точка в конце наименования таблицы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import TABLE_ENVIRONMENTS, caption_findings, one_line


@rule(
    id="table-caption-dot",
    standards={G732: "6.6.3"},
    severity=Severity.ERROR,
    title="Наименование таблицы заканчивается точкой",
    fixable=True,
    deprecated_ids=("G732-6.6.3-caption-dot",),
)
def table_caption_dot(doc: Document) -> Iterable[Finding]:
    r"""Проверяет наименование таблицы на точку в конце.

    ## Почему это нарушение

    Наименование таблицы приводят с прописной буквы без точки в конце.

    ## Как исправить

    Убрать точку в конце `\caption`.
    """

    def check(text: str) -> tuple[str, str] | None:
        if not text.endswith("."):
            return None
        return "Наименование таблицы заканчивается точкой.", one_line(text[:-1])

    return caption_findings(
        table_caption_dot,
        doc,
        TABLE_ENVIRONMENTS,
        requirement="Наименование таблицы приводят с прописной буквы без точки в конце.",
        check=check,
    )
