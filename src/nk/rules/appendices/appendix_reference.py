"""Ссылка в тексте на каждое приложение."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import (
    APPENDIX_REFERENCE,
    heading_text,
    is_full_document,
    normalize_heading,
    ordered_headings,
)

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+([А-Я])$")


@rule(
    id="appendix-no-reference",
    standards={G732: "6.17.2"},
    severity=Severity.ERROR,
    title="На приложение нет ссылки в тексте",
    deprecated_ids=("G732-6.17.2-appendix-no-reference",),
)
def appendix_no_reference(doc: Document) -> Iterable[Finding]:
    """Собирает буквы приложений из заголовков и упоминания вида «в приложении А» из
    текста. Приложение без упоминания — находка. Правило работает только на полном
    документе: по отдельному файлу главы судить о ссылках нельзя.

    ## Почему это нарушение

    Приложение — продолжение текста, а не приложенный к нему материал: на каждое
    приложение в отчёте даётся ссылка, и располагают приложения в порядке ссылок.
    Приложение, на которое никто не ссылается, в отчёте не нужно.

    ## Как исправить

    Сослаться на приложение в том месте, где оно по смыслу требуется, либо убрать
    приложение из отчёта.
    """
    if not is_full_document(doc):
        return

    referenced = {
        match.group(1)
        for line in doc.iter_lines()
        for match in APPENDIX_REFERENCE.finditer(line.stripped)
    }
    for command in ordered_headings(doc):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        letter = match.group(1)
        if letter in referenced:
            continue
        yield appendix_no_reference.finding(
            doc,
            command.span,
            message=f"На приложение {letter} в тексте нет ссылки.",
            requirement=(
                "В тексте отчёта на все приложения должны быть даны ссылки; "
                "приложения располагают в порядке ссылок на них."
            ),
            suggestion=f"Добавить в текст ссылку: приведено в приложении {letter}.",
            col=command.col,
        )
