"""Номер рисунка, вписанный в наименование вручную."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import FIGURE_ENVIRONMENTS, caption_findings, one_line

#: «Рисунок 1 — », «Рис. 2.1 -», «Рисунок А.3.»
MANUAL_NUMBER = re.compile(r"^\s*(?:Рисунок|Рис\.)\s*[0-9А-ЯA-Z][0-9.]*\s*[-–—:.]?\s*")


@rule(
    id="figure-caption-manual-number",
    standards={G732: "6.5.7", GR2105: "6.9.3"},
    severity=Severity.ERROR,
    title="Номер рисунка вписан в наименование вручную",
    fixable=True,
    deprecated_ids=("G732-6.5.7-caption-manual-number",),
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

    def check(text: str) -> tuple[str, str] | None:
        match = MANUAL_NUMBER.match(text)
        if match is None:
            return None
        found = one_line(match.group(0))
        return f"Наименование начинается с «{found}» — номер вписан вручную.", one_line(
            text[match.end() :]
        )

    return caption_findings(
        figure_caption_manual_number,
        doc,
        FIGURE_ENVIRONMENTS,
        requirement=(
            "Слово «Рисунок», номер и тире формирует класс документа; "
            "в наименовании оставляют только сам текст."
        ),
        check=check,
    )
