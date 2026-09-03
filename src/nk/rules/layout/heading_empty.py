"""Раздел без заголовка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import SECTION_DEPTH, heading_text, headings, visible_text

#: Пункты и подпункты заголовков, как правило, не имеют.
TITLED_DEPTH = 2


@rule(
    id="G732-6.2.2-heading-empty",
    clause="6.2.2",
    severity=Severity.ERROR,
    title="Раздел или подраздел без заголовка",
)
def heading_empty(doc: Document) -> Iterable[Finding]:
    for command in headings(doc):
        if SECTION_DEPTH[command.name] > TITLED_DEPTH:
            continue
        if visible_text(heading_text(command)).strip():
            continue
        yield heading_empty.finding(
            doc,
            command.span,
            message=f"У команды \\{command.name} пустой заголовок.",
            requirement="Разделы и подразделы отчёта должны иметь заголовки.",
            suggestion="Указать заголовок, отражающий содержание раздела.",
            col=command.col,
        )
