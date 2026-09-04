"""Точка в конце наименования рисунка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, caption_findings, one_line


@rule(
    id="G732-6.5.7-caption-dot",
    clause="6.5.7",
    severity=Severity.ERROR,
    title="Наименование рисунка заканчивается точкой",
    fixable=True,
)
def figure_caption_dot(doc: Document) -> Iterable[Finding]:
    r"""Проверяет наименование рисунка на точку в конце. Точка внутри наименования
    нарушением не является.

    ## Почему это нарушение

    Наименование рисунка приводят с прописной буквы без точки в конце: оно
    образует с номером единую подпись, а не предложение.

    ## Как исправить

    Убрать точку в конце `\caption`.
    """

    def check(text: str) -> tuple[str, str] | None:
        if not text.endswith("."):
            return None
        return "Наименование рисунка заканчивается точкой.", one_line(text[:-1])

    return caption_findings(
        figure_caption_dot,
        doc,
        FIGURE_ENVIRONMENTS,
        requirement="Наименование рисунка приводят с прописной буквы без точки в конце.",
        check=check,
    )
