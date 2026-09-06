"""Приложение, не начатое с новой страницы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import (
    appendix_spans,
    leading_text,
    page_break_fix,
    previous_content,
    starts_page,
)


@rule(
    id="appendix-page-break",
    standards={G732: "6.17.3", GR2105: "6.3.4"},
    severity=Severity.ERROR,
    title="Приложение не начинается с новой страницы",
    fixable=True,
    deprecated_ids=("G732-6.17.3-appendix-page-break",),
)
def appendix_page_break(doc: Document) -> Iterable[Finding]:
    """Проверяет разрыв страницы перед заголовком приложения.

    ## Почему это нарушение

    Каждое приложение размещают с новой страницы. Заголовок, оформленный
    через `\\section*`, разрыва страницы сам не даёт ни в одном классе
    документа — его ставят явно.

    ## Как исправить

    Добавить `\\newpage` перед заголовком приложения.
    """
    for command, letter, _ in appendix_spans(doc):
        leading = leading_text(doc, command)
        previous = previous_content(doc, command)
        if starts_page(leading) if leading else previous is None or starts_page(previous):
            continue
        yield appendix_page_break.finding(
            doc,
            command.span,
            message=f"Перед приложением {letter} нет разрыва страницы.",
            requirement="Каждое приложение размещают с новой страницы.",
            suggestion="\\newpage",
            col=command.col,
            fix=page_break_fix(doc, command),
        )
