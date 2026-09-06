"""Раздел без заголовка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import heading_level, heading_text, headings, visible_text

#: Пункты и подпункты заголовков, как правило, не имеют.
TITLED_DEPTH = 2


@rule(
    id="heading-empty",
    standards={G732: "6.2.2", GR2105: "6.6.1"},
    severity=Severity.ERROR,
    title="Раздел или подраздел без заголовка",
    deprecated_ids=("G732-6.2.2-heading-empty",),
)
def heading_empty(doc: Document) -> Iterable[Finding]:
    """Ищет разделы и подразделы с пустым заголовком: команда есть, текста в ней нет
    либо остались одни команды оформления. Пункты и подпункты, которые заголовка,
    как правило, не имеют, не проверяются.

    ## Почему это нарушение

    Разделы и подразделы должны иметь заголовки, отражающие их содержание: по ним
    строится содержание отчёта.

    ## Как исправить

    Указать заголовок. Если рубрика нужна только для отступа или разрыва
    страницы, оформить её средствами вёрстки, а не пустым разделом.
    """
    for command in headings(doc):
        if heading_level(doc, command) > TITLED_DEPTH:
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
