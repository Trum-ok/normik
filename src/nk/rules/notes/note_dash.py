"""Знак после слова «Примечание»."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import DASH
from nk.rules._text import is_code

#: Единственное примечание: слово, затем разделитель и текст в той же строке.
SINGLE_NOTE = re.compile(r"^\s*Примечание(?P<gap>\s*)(?P<rest>\S.*)$")
WRONG_SEPARATORS = ":.-–"


@rule(
    id="note-dash",
    standards={G732: "6.7.3", GR2105: "6.12.3"},
    severity=Severity.ERROR,
    title="После слова «Примечание» стоит не тире",
    fixable=True,
    deprecated_ids=("G732-6.7.3-note-dash",),
)
def note_dash(doc: Document) -> Iterable[Finding]:
    """Проверяет знак между словом «Примечание» и его текстом.

    ## Почему это нарушение

    Если примечание одно, после слова «Примечание» ставится тире, а сам текст
    печатается с прописной буквы. Двоеточие и точка стандартом не предусмотрены.

    ## Как исправить

    Поставить тире: `Примечание — Текст примечания.`

    Форма для нескольких примечаний — слово «Примечания» отдельной строкой
    и нумерованный список под ним — правилом не затрагивается. Листинги
    и таблицы правило не просматривает: там это содержимое кода или ячейки.

    Строка, где «Примечание» — обычное слово предложения, правилом тоже не
    затрагивается: без разделителя примечание опознаётся только по прописной
    букве сразу за словом, а «Примечание, приведённое выше» или «Примечанием
    считают» остаются как есть.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        match = SINGLE_NOTE.match(line.stripped)
        if match is None:
            continue
        rest = match.group("rest")
        if rest.startswith(DASH):
            continue

        start = match.start("gap") + 1
        if rest[0] in WRONG_SEPARATORS:
            # За разделителем должен идти текст примечания: «Примечание.» —
            # это конец обычного предложения, а не заголовок примечания.
            if not rest[1:].strip():
                continue
            end = match.start("rest") + 2
            replacement = f" {DASH}"
            found = f"«{rest[0]}»"
        else:
            # Без разделителя примечание опознаётся по пробелу и прописной
            # букве: иначе «Примечание, приведённое выше» и «Примечанием
            # считают» разбирались бы как примечание без знака.
            if not match.group("gap") or not rest[0].isupper():
                continue
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
