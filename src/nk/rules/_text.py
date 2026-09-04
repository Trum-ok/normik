"""Помощники для правил, работающих по тексту строки.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from nk.core.document import Document, Line
from nk.core.finding import Fix
from nk.core.position import Region
from nk.rules._shared import NBSP

#: Окружения, содержимое которых типографике не подчиняется.
CODE_ENVIRONMENTS = frozenset(
    {"verbatim", "Verbatim", "lstlisting", "minted", "alltt", "tabular", "tabular*", "tabularx"}
)

_COMMAND_ARG = re.compile(
    r"(\\(?:label|ref|eqref|autoref|cite\w*|input|include|includegraphics|url|href))\s*\{[^{}]*\}"
)


def prose(doc: Document, line: Line) -> str:
    """Строка без формул и технических аргументов, с сохранением длины.

    Формула типографике не подчиняется: дефис в ней знак вычитания, кавычки —
    штрихи. Границы формул размечены при разборе, поэтому строчной и выключной
    математики здесь не остаётся ни в каком виде.

    Позиции находок считаются по исходной строке, поэтому вырезанное
    заменяется пробелами, а не удаляется.
    """
    text = doc.math.mask(line.path, line.lineno, line.stripped)
    # Имя команды сохраняется: для типографики важно, что идёт после пробела.
    return _COMMAND_ARG.sub(
        lambda match: match.group(1) + " " * (len(match.group(0)) - len(match.group(1))),
        text,
    )


@dataclass(frozen=True, slots=True)
class Gap:
    """Разрывный пробел, найденный по шаблону: где он и чем его заменить."""

    line: Line
    col: int
    fix: Fix
    found: str
    """Текст совпадения без окружающих пробелов — его называют в сообщении."""


def gaps(doc: Document, pattern: re.Pattern[str]) -> Iterator[Gap]:
    """Разрывные пробелы по шаблону: группа 1 — сам пробел, который надо заменить.

    Правила о неразрывном пробеле различаются только шаблоном и формулировками:
    обход строк, пропуск кода, разбор по прозе и сборка правки у них общие.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in pattern.finditer(prose(doc, line)):
            start, end = match.span(1)
            yield Gap(
                line=line,
                col=start + 1,
                fix=Fix(Region.in_line(line.path, line.lineno, start + 1, end + 1), NBSP),
                found=match.group(0).strip(),
            )


def is_code(doc: Document, line: Line) -> bool:
    """Находится ли строка внутри окружения, к которому типографика неприменима.

    Проверяются все охватывающие окружения, а не только внутреннее: ячейка
    ``tabular`` лежит внутри ``table``, а листинг — внутри ``figure``.
    """
    return (line.path, line.lineno) in doc.structure.covered_lines(*CODE_ENVIRONMENTS)
