"""Номер рисунка, вписанный в наименование вручную."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, caption_text, captions, one_line

#: «Рисунок 1 — », «Рис. 2.1 -», «Рисунок А.3.»
MANUAL_NUMBER = re.compile(r"^\s*(?:Рисунок|Рис\.)\s*[0-9А-ЯA-Z][0-9.]*\s*[-–—:.]?\s*")


@rule(
    id="G732-6.5.7-caption-manual-number",
    clause="6.5.7",
    severity=Severity.ERROR,
    title="Номер рисунка вписан в наименование вручную",
    fixable=True,
)
def figure_caption_manual_number(doc: Document) -> Iterable[Finding]:
    r"""Ищет наименования, начинающиеся со слова «Рисунок» или сокращения «Рис.»
    с номером: номер вписан руками, хотя его формирует класс документа.

    ## Почему это нарушение

    Слово «Рисунок», номер и тире подставляются автоматически. Вписанный руками
    номер даёт в документе двойную подпись вида «Рисунок 3 — Рисунок 1 — Схема»
    и расходится с автоматической нумерацией при вставке иллюстрации.

    ## Как исправить

    Оставить в `\caption` только текст наименования, а ссылаться на рисунок
    через метку.
    """
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        for command in captions(environment):
            text = caption_text(command)
            match = MANUAL_NUMBER.match(text)
            if match is None:
                continue
            rest = one_line(text[match.end() :])
            yield figure_caption_manual_number.finding(
                doc,
                command.span,
                message=f"Наименование начинается с «{one_line(match.group(0))}» — номер вписан вручную.",
                requirement=(
                    "Слово «Рисунок», номер и тире формирует класс документа; "
                    "в наименовании оставляют только сам текст."
                ),
                suggestion=f"\\{command.name}{{{rest}}}",
                col=command.col,
                fix=command.region,
            )
