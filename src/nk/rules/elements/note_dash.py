"""Знак после слова «Примечание»."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule

DASH = "—"
#: Единственное примечание: слово, затем разделитель и текст в той же строке.
SINGLE_NOTE = re.compile(r"^\s*Примечание(?P<gap>\s*)(?P<rest>\S.*)$")
WRONG_SEPARATORS = ":.-–"


@rule(
    id="G732-6.7.3-note-dash",
    clause="6.7.3",
    severity=Severity.ERROR,
    title="После слова «Примечание» стоит не тире",
    fixable=True,
)
def note_dash(doc: Document) -> Iterable[Finding]:
    """Проверяет знак между словом «Примечание» и его текстом.

    ## Почему это нарушение

    Если примечание одно, после слова «Примечание» ставится тире, а сам текст
    печатается с прописной буквы. Двоеточие и точка стандартом не предусмотрены.

    ## Как исправить

    Поставить тире: `Примечание — Текст примечания.`

    Форма для нескольких примечаний — слово «Примечания» отдельной строкой
    и нумерованный список под ним — правилом не затрагивается.
    """
    for line in doc.iter_lines():
        match = SINGLE_NOTE.match(line.stripped)
        if match is None:
            continue
        rest = match.group("rest")
        if rest.startswith(DASH):
            continue

        start = match.start("gap") + 1
        if rest[0] in WRONG_SEPARATORS:
            end = match.start("rest") + 2
            replacement = f" {DASH}"
            found = f"«{rest[0]}»"
        else:
            end = match.start("rest") + 1
            replacement = f" {DASH} "
            found = "ничего"

        yield note_dash.finding(
            doc,
            line,
            message=f"После слова «Примечание» стоит {found}, а не тире.",
            requirement=(
                "Если примечание одно, после слова «Примечание» ставится тире, "
                "а текст печатается с прописной буквы."
            ),
            suggestion=f"Примечание {DASH} {rest.lstrip(WRONG_SEPARATORS + ' ')}",
            col=start,
            fix=Fix(Region.in_line(line.path, line.lineno, start, end), replacement),
        )
