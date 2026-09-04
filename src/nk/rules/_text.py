"""Помощники для правил, работающих по тексту строки.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила.
"""

import re

from nk.core.document import Document, Line

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


def is_code(doc: Document, line: Line) -> bool:
    """Находится ли строка внутри окружения, к которому типографика неприменима.

    Проверяются все охватывающие окружения, а не только внутреннее: ячейка
    ``tabular`` лежит внутри ``table``, а листинг — внутри ``figure``.
    """
    return (line.path, line.lineno) in doc.structure.covered_lines(*CODE_ENVIRONMENTS)
