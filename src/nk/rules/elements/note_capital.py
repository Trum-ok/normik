"""Слово «Примечание» со строчной буквы."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule

#: Строка, начинающаяся со слова «Примечание» или «Примечания».
NOTE_HEADER = re.compile(r"^\s*(примечани[ея])\b", re.IGNORECASE)


@rule(
    id="G732-6.7.2-note-capital",
    clause="6.7.2",
    severity=Severity.ERROR,
    title="Слово «Примечание» набрано со строчной буквы",
    fixable=True,
)
def note_capital(doc: Document) -> Iterable[Finding]:
    """Проверяет регистр слова, которым начинается примечание.

    ## Почему это нарушение

    Слово «Примечание» — заголовок примечания, а не часть фразы: его печатают
    с прописной буквы с абзацного отступа.

    ## Как исправить

    Заменить первую букву на прописную.
    """
    for line in doc.iter_lines():
        match = NOTE_HEADER.match(line.stripped)
        if match is None:
            continue
        word = match.group(1)
        if not word[0].islower():
            continue
        col = match.start(1) + 1
        yield note_capital.finding(
            doc,
            line,
            message=f"Примечание начинается со строчной буквы: «{word}».",
            requirement="Слово «Примечание» печатают с прописной буквы с абзацного отступа.",
            suggestion=f"{word[0].upper()}{word[1:]}",
            col=col,
            fix=Fix(Region.in_line(line.path, line.lineno, col, col + 1), word[0].upper()),
        )
