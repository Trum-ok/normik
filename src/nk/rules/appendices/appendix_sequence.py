"""Последовательность обозначений приложений."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    heading_text,
    normalize_heading,
    ordered_headings,
)

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+(\S+)$")


@rule(
    id="G732-6.17.4-appendix-sequence",
    clause="6.17.4",
    severity=Severity.ERROR,
    title="В обозначениях приложений пропущена буква",
    fixable=True,
)
def appendix_sequence(doc: Document) -> Iterable[Finding]:
    """Идёт по заголовкам приложений в порядке следования и сверяет обозначение
    с ожидаемым: после А идёт Б, после Б — В, с пропуском букв, которые в
    обозначениях не используются. Набор обозначений и их порядок задаёт
    [профиль](../profiles.md#обозначения-приложений); обозначение вне набора
    пропускается — о нём сообщает отдельное правило.

    ## Почему это нарушение

    Пропуск в последовательности читается как потерянное приложение: читающий ищет
    приложение Б, которого в отчёте нет.

    ## Как исправить

    Перенумеровать приложения подряд начиная с А. Если приложение убрано,
    обозначения следующих сдвигаются.
    """
    letters = doc.profile.appendix_letters
    position = 0
    for command in ordered_headings(doc):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        letter = match.group(1)
        if letter not in letters:
            continue
        expected = letters[position]
        if letter == expected:
            position += 1
            continue
        yield appendix_sequence.finding(
            doc,
            command.span,
            message=f"После предыдущего приложения ожидалось «{expected}», а стоит «{letter}».",
            requirement=(
                f"Приложения обозначают по порядку начиная с «{letters[0]}», "
                "не пропуская последовательность."
            ),
            suggestion=f"\\{command.name}{{ПРИЛОЖЕНИЕ {expected}}}",
            col=command.col,
            fix=command.region,
        )
        position = letters.index(letter) + 1
