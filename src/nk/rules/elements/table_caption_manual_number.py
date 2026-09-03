"""Номер таблицы, вписанный в наименование вручную."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import TABLE_ENVIRONMENTS, caption_text, captions, one_line

#: «Таблица 1 — », «Табл. 2.3 -», «Таблица А.1»
MANUAL_NUMBER = re.compile(r"^\s*(?:Таблица|Табл\.)\s*[0-9А-ЯA-Z][0-9.]*\s*[-–—:.]?\s*")


@rule(
    id="G732-6.6.3-caption-manual-number",
    clause="6.6.3",
    severity=Severity.ERROR,
    title="Номер таблицы вписан в наименование вручную",
)
def table_caption_manual_number(doc: Document) -> Iterable[Finding]:
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            match = MANUAL_NUMBER.match(text)
            if match is None:
                continue
            rest = one_line(text[match.end() :])
            yield table_caption_manual_number.finding(
                doc,
                command.span,
                message=f"Наименование начинается с «{one_line(match.group(0))}» — номер вписан вручную.",
                requirement=(
                    "Слово «Таблица», номер и тире формирует класс документа; "
                    "в наименовании оставляют только сам текст."
                ),
                suggestion=f"\\{command.name}{{{rest}}}",
                col=command.col,
            )
