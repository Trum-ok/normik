"""Помощники для правил, работающих по тексту строки.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from nk.core.document import Document, Line
from nk.core.finding import Fix
from nk.core.latex import literal_end
from nk.core.position import Region
from nk.rules._shared import NBSP

#: Единицы физических величин. Сокращения вроде «с.» и «рис.» сюда не входят:
#: правила об единицах касаются только величин.
PHYSICAL_UNITS = [
    "мкм",
    "нм",
    "мм",
    "см",
    "дм",
    "км",
    "м",
    "мг",
    "кг",
    "г",
    "т",
    "мл",
    "л",
    "мин",
    "ч",
    "сут",
    "Гц",
    "кГц",
    "МГц",
    "ГГц",
    "Вт",
    "кВт",
    "мВт",
    "кВ",
    "мВ",
    "В",
    "мА",
    "А",
    "кОм",
    "Ом",
    "кДж",
    "МДж",
    "Дж",
    "кПа",
    "МПа",
    "Па",
    "кН",
    "Н",
    "К",
]

#: Окружения, содержимое которых типографике не подчиняется.
CODE_ENVIRONMENTS = frozenset(
    {"verbatim", "Verbatim", "lstlisting", "minted", "alltt", "tabular", "tabular*", "tabularx"}
)

_COMMAND_ARG = re.compile(
    r"(\\(?:label|ref|eqref|autoref|cite\w*|input|include|includegraphics|url|href"
    # texttt и path набирают путь или имя команды: тире и ёлочки в них — порча.
    r"|texttt|path))\s*\{[^{}]*\}"
)

#: Команды, аргумент которых набирается буквально, с разделителем вместо скобок.
_LITERAL = re.compile(r"\\(verb\*?|lstinline|mintinline)")


def prose(doc: Document, line: Line) -> str:
    """Строка без формул и технических аргументов, с сохранением длины.

    Формула типографике не подчиняется: дефис в ней знак вычитания, кавычки —
    штрихи. Границы формул размечены при разборе, поэтому строчной и выключной
    математики здесь не остаётся ни в каком виде.

    Позиции находок считаются по исходной строке, поэтому вырезанное
    заменяется пробелами, а не удаляется.
    """
    text = _mask_literals(doc.math.mask(line.path, line.lineno, line.stripped))
    # Имя команды сохраняется: для типографики важно, что идёт после пробела.
    return _COMMAND_ARG.sub(
        lambda match: match.group(1) + " " * (len(match.group(0)) - len(match.group(1))),
        text,
    )


def _mask_literals(text: str) -> str:
    """Заменить пробелами буквальные вставки, оставив имена команд.

    Аргумент ``\\verb`` и его родни набирается как есть: неразрывный пробел или
    ёлочка, поставленные туда правкой, попали бы в отчёт буквально.
    """
    parts = list(text)
    position = 0
    while (match := _LITERAL.search(text, position)) is not None:
        end = _literal_end(text, match.group(1), match.end())
        parts[match.end() : end] = " " * (end - match.end())
        position = max(end, match.end())
    return "".join(parts)


def _literal_end(text: str, name: str, index: int) -> int:
    """Позиция сразу за буквальной вставкой, считая от конца имени команды."""
    index = _group_end(text, index, "[]")
    if name == "mintinline":
        # Первая группа — язык подсветки, буквально набирается вторая.
        index = _group_end(text, index, "{}")
    if index < len(text) and text[index] == "{":
        return _group_end(text, index, "{}")

    end = literal_end(text, index)
    # Разделителя нет: вставки здесь не начинается, маскировать нечего.
    return index if end is None else end


def _group_end(text: str, index: int, pair: str) -> int:
    """Позиция за группой, если она начинается на ``index``, иначе сам ``index``."""
    if index >= len(text) or text[index] != pair[0]:
        return index
    close = text.find(pair[1], index + 1)
    return index if close == -1 else close + 1


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
