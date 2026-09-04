"""Последовательность обозначений приложений."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    APPENDIX_LETTERS,
    SECTION_DEPTH,
    heading_text,
    normalize_heading,
    ordered_commands,
)

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+([А-Я])$")


@rule(
    id="G732-6.17.4-appendix-sequence",
    clause="6.17.4",
    severity=Severity.ERROR,
    title="В обозначениях приложений пропущена буква",
    fixable=True,
)
def appendix_sequence(doc: Document) -> Iterable[Finding]:
    """Идёт по заголовкам приложений в порядке следования и сверяет букву с ожидаемой:
    после А идёт Б, после Б — В, с пропуском букв, которые в обозначениях не
    используются.

    ## Почему это нарушение

    Пропуск в последовательности читается как потерянное приложение: читающий ищет
    приложение Б, которого в отчёте нет.

    ## Как исправить

    Перенумеровать приложения подряд начиная с А. Если приложение убрано,
    обозначения следующих сдвигаются.
    """
    position = 0
    for command in ordered_commands(doc, *SECTION_DEPTH):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        letter = match.group(1)
        if letter not in APPENDIX_LETTERS:
            continue
        expected = APPENDIX_LETTERS[position]
        if letter == expected:
            position += 1
            continue
        yield appendix_sequence.finding(
            doc,
            command.span,
            message=f"После предыдущего приложения ожидалось «{expected}», а стоит «{letter}».",
            requirement=(
                "Приложения обозначают буквами кириллицы начиная с А, "
                "не пропуская последовательность."
            ),
            suggestion=f"\\{command.name}{{ПРИЛОЖЕНИЕ {expected}}}",
            col=command.col,
            fix=command.region,
        )
        position = APPENDIX_LETTERS.index(letter) + 1
