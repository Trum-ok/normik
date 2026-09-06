"""Слово рубрики в её собственном заголовке."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_text, headings, normalize_heading, structural_element

#: Слова, называющие саму рубрику: их место в номере, а не в заголовке.
RUBRIC_WORDS = ("ГЛАВА", "РАЗДЕЛ", "ПОДРАЗДЕЛ", "ПУНКТ", "ПОДПУНКТ")

#: Слово рубрики в начале заголовка, дальше — номер либо наименование.
_RUBRIC_START = re.compile(r"^(" + "|".join(RUBRIC_WORDS) + r")\b")


@rule(
    id="heading-rubric-word",
    severity=Severity.WARNING,
    title="Заголовок начинается со слова «глава» или «раздел»",
    fixable=True,
    default_off=True,
)
def heading_rubric_word(doc: Document) -> Iterable[Finding]:
    r"""Ищет заголовки, начатые словом, которое называет саму рубрику. Заголовки
    структурных элементов не проверяются: «ПРИЛОЖЕНИЕ А» — их собственное
    наименование, а не рубрика основной части.

    Ни один из стандартов такого запрета не содержит, поэтому правило выключено
    по умолчанию. Включают его профилем того вуза, чьё положение этого требует.

    ## Почему это нарушение

    Что перед читающим раздел, видно по номеру и по месту заголовка. Слово
    «Раздел» в самом заголовке повторяет номер и отнимает место у наименования.

    ## Как исправить

    Убрать слово рубрики из заголовка, оставив наименование.
    """
    for command in headings(doc):
        text = heading_text(command)
        if structural_element(doc, text) is not None:
            continue
        match = _RUBRIC_START.match(normalize_heading(text))
        if match is None:
            continue
        word = match.group(1)
        yield heading_rubric_word.finding(
            doc,
            command.span,
            message=f"Заголовок начинается со слова «{word.capitalize()}».",
            requirement=("Слова «глава», «раздел», «подраздел» и «пункт» в заголовках не пишут."),
            suggestion=f"\\{command.name}{{{_without(text, word)}}}",
            col=command.col,
            fix=command.region,
        )


def _without(text: str, word: str) -> str:
    """Заголовок без слова рубрики и следующего за ним номера."""
    tail = re.sub(r"^\s*[\wА-Яа-яЁё]+\s*[\d.]*\s*[-—–.:]?\s*", "", text, count=1)
    return tail.strip() or text.strip()
