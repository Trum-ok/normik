"""Номер таблицы, вписанный в наименование вручную."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import TABLE_ENVIRONMENTS, caption_findings, one_line

#: «Таблица 1 — », «Табл. 2.3 -», «Таблица А.1»
MANUAL_NUMBER = re.compile(r"^\s*(?:Таблица|Табл\.)\s*[0-9А-ЯA-Z][0-9.]*\s*[-–—:.]?\s*")


@rule(
    id="table-caption-manual-number",
    standards={G732: "6.6.3", GR2105: "6.8.2"},
    severity=Severity.ERROR,
    title="Номер таблицы вписан в наименование вручную",
    fixable=True,
    deprecated_ids=("G732-6.6.3-caption-manual-number",),
)
def table_caption_manual_number(doc: Document) -> Iterable[Finding]:
    r"""Ищет наименования, начинающиеся со слова «Таблица» или сокращения «Табл.»
    с номером.

    ## Почему это нарушение

    Слово «Таблица», номер и тире подставляются автоматически. Вписанный руками
    номер удваивает подпись и расходится с автоматической нумерацией.

    ## Как исправить

    Оставить в `\caption` только текст наименования.
    """

    def check(text: str) -> tuple[str, str] | None:
        match = MANUAL_NUMBER.match(text)
        if match is None:
            return None
        found = one_line(match.group(0))
        return f"Наименование начинается с «{found}» — номер вписан вручную.", one_line(
            text[match.end() :]
        )

    return caption_findings(
        table_caption_manual_number,
        doc,
        TABLE_ENVIRONMENTS,
        requirement=(
            "Слово «Таблица», номер и тире формирует класс документа; "
            "в наименовании оставляют только сам текст."
        ),
        check=check,
    )
