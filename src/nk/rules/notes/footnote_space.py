"""Пробел перед знаком сноски."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732

FOOTNOTE_COMMANDS = ("footnote", "footnotemark")


@rule(
    id="footnote-space",
    standards={G732: "6.7.4"},
    severity=Severity.ERROR,
    title="Знак сноски отделён пробелом от поясняемого слова",
    fixable=True,
    deprecated_ids=("G732-6.7.4-footnote-space",),
)
def footnote_space(doc: Document) -> Iterable[Finding]:
    """Проверяет, что сноска стоит вплотную к слову, к которому относится.

    ## Почему это нарушение

    Знак сноски ставят без пробела непосредственно после слова, числа или
    символа, к которому даётся пояснение. Пробел отрывает знак от слова
    и в наборе выглядит как отдельный символ.

    ## Как исправить

    Убрать пробел перед `\\footnote`.
    """
    for command in doc.structure.find_commands(*FOOTNOTE_COMMANDS):
        line = doc.line_at(command.path, command.lineno)
        if line is None or command.col < 2:
            continue
        before = line.raw[: command.col - 1]
        stripped = before.rstrip(" \t")
        if len(stripped) == len(before) or not stripped:
            continue
        backslashes = len(stripped) - len(stripped.rstrip("\\"))
        if backslashes and backslashes % 2 == 0:
            # Перед пробелом «\\»: знак сноски и так начинает новую строку,
            # отрывать его от слова тут нечему.
            continue
        # Нечётная косая — команда пробела «\ »: убирать нужно её целиком,
        # иначе остаток слипнется со сноской в «\\footnote».
        start = len(stripped) + 1 - backslashes % 2
        yield footnote_space.finding(
            doc,
            command.span,
            message="Между словом и знаком сноски стоит пробел.",
            requirement=(
                "Знак сноски ставят без пробела непосредственно после слова, "
                "к которому даётся пояснение."
            ),
            suggestion="Убрать пробел перед знаком сноски.",
            col=start,
            fix=Fix(Region.in_line(line.path, line.lineno, start, command.col), ""),
        )
