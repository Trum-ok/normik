"""Помощники правил о библиографическом описании.

Описание источника — не проза. Пунктуация в нём предписанная: двоеточие,
косая черта и точка с тире опознают области и элементы описания, а не
разделяют части предложения. Поэтому запись здесь собирается целиком — от
``\\bibitem`` до следующего, — и уже по ней правила ищут знаки: элемент
переносится на другую строку исходника сколько угодно раз, а описание
остаётся одним.

Разметка LaTeX из записи не забивается пробелами, а выбрасывается: правило
обязано видеть ровно то, что видит читатель отчёта. Иначе закрывающая скобка
группы читалась бы как пробел, и после ``\\url{…}`` находился бы лишний пробел
перед точкой, которого в наборе нет. Взамен каждый знак записи помнит свою
колонку в исходнике: по ней находка указывает место, а правка находит, что
заменять.

Проверяется только список, набранный в исходнике: у списка, собираемого
BibTeX, описаний в ``.tex`` нет вовсе — об этом сообщает отдельное правило
``bibtex-order-unverifiable``.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from nk.core.document import Command, Document, Line
from nk.core.position import Position, Region
from nk.rules._shared import BIBITEM_COMMAND, BIBLIOGRAPHY_ENVIRONMENT

#: Тире между областями описания в наборе. ГОСТ рисует короткое тире, в
#: исходнике его набирают и знаком, и лигатурой ``--``.
EN_DASH = "–"

#: Сетевой адрес: предписанной пунктуации внутри него нет — там косые черты и
#: двоеточия принадлежат самому адресу. Хвостовые точка и запятая в адрес не
#: входят: это уже знаки описания.
URL = re.compile(r"(?:https?://|ftp://|www\.)\S*[^\s.,;:]", re.IGNORECASE)

#: Идентификатор DOI: как и адрес, внутри себя знаков описания не содержит.
DOI = re.compile(r"\b10\.\d{4,9}/\S*[^\s.,;:]")

#: Чем закрывают участок, внутри которого знаков описания не ищут. Заглушка не
#: пробел: закрытый участок — это адрес или идентификатор, то есть непрерывный
#: кусок текста, и знак рядом с ним отделён от него не больше, чем от слова.
FILLER = "\x00"

_COMMAND = re.compile(r"\\[A-Za-z]+\*?")

#: Обратная косая перед незначащим знаком: сама она в набор не попадает.
_ESCAPE = re.compile(r"\\(?=[^A-Za-z])")

#: Знаки, которых в наборе не видно: скобки групп и границы формул.
_INVISIBLE = "{}$"

#: Знаки, которые печатаются пробелом. Неразрывность на пунктуацию не влияет.
_AS_SPACE = "~"


@dataclass(frozen=True, slots=True)
class Part:
    """Часть описания, попавшая в одну строку исходника."""

    line: Line
    text: str
    """То, что печатается: разметка выброшена, «~» заменён пробелом."""

    columns: tuple[int, ...]
    """Колонка исходника для каждого знака :attr:`text`."""

    offset: int
    """Позиция начала части в тексте всей записи."""

    end: int
    """Колонка исходника сразу за последним непробельным знаком части.

    Считая и разметку: точка, дописанная в конец описания, должна встать за
    закрывающей скобкой ``\\url{…}``, а не внутри группы.
    """


@dataclass(frozen=True, slots=True)
class Entry:
    """Библиографическое описание одного источника."""

    key: str
    parts: tuple[Part, ...]
    text: str
    """Описание целиком, одной строкой: по нему ищут знаки предписанной пунктуации."""

    def at(self, index: int) -> tuple[Line, int]:
        """Строка исходника и колонка в ней по позиции в тексте записи."""
        part = self._part(index)
        local = index - part.offset
        if local < len(part.columns):
            return part.line, part.columns[local]
        # Позиция пришлась на перевод строки: указываем на конец строки.
        return part.line, part.end

    def region(self, start: int, end: int) -> Region | None:
        """Регион исходника под участком ``[start, end)`` записи.

        ``None`` — участок не укладывается в одну строку исходника либо внутри
        него осталась разметка. Правка ни тем, ни другим не распоряжается: она
        заменяет знаки, а не склеивает строки и не стирает команды.
        """
        part = self._part(start)
        last = end - 1 - part.offset
        if part is not self._part(end - 1) or not 0 <= last < len(part.columns):
            return None
        first = part.columns[start - part.offset]
        stop = part.columns[last] + 1
        if stop - first != end - start:
            return None
        return Region.in_line(part.line.path, part.line.lineno, first, stop)

    @property
    def tail(self) -> tuple[Line, int] | None:
        """Строка и колонка сразу за последним знаком описания."""
        for part in reversed(self.parts):
            if part.text.strip():
                return part.line, part.end
        return None

    def _part(self, index: int) -> Part:
        found = self.parts[0]
        for candidate in self.parts:
            if candidate.offset > index:
                break
            found = candidate
        return found


def entries(doc: Document) -> Iterator[Entry]:
    """Описания из списков источников, набранных в исходнике."""
    for bibliography in doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT):
        items = sorted(
            (
                command
                for command in bibliography.all_commands()
                if command.name == BIBITEM_COMMAND and command.arg
            ),
            key=lambda command: (command.lineno, command.col),
        )
        ends = [
            *(Position(command.lineno, command.col) for command in items[1:]),
            Position(bibliography.span.end, 1),
        ]
        for command, end in zip(items, ends, strict=True):
            entry = _entry(doc, command, end)
            if entry is not None:
                yield entry


def mask(text: str, *pattern: re.Pattern[str]) -> str:
    """Текст, где совпадения шаблонов закрыты знаком-заглушкой.

    Длина сохраняется: колонки находок считаются по той же позиции, что и до
    маскирования.
    """
    chars = list(text)
    for item in pattern:
        for match in item.finditer(text):
            chars[match.start() : match.end()] = FILLER * (match.end() - match.start())
    return "".join(chars)


def _entry(doc: Document, command: Command, end: Position) -> Entry | None:
    if command.region is None:
        # Границ у команды нет: её собрал не разбор исходника. Где кончается
        # \bibitem и начинается описание, узнать тогда неоткуда.
        return None
    start = command.region.end
    parts: list[Part] = []
    offset = 0
    for line in doc.lines_of(command.path)[start.lineno - 1 : end.lineno]:
        source = doc.math.mask(line.path, line.lineno, line.stripped)
        first = min(start.col - 1 if line.lineno == start.lineno else 0, len(source))
        last = min(end.col - 1 if line.lineno == end.lineno else len(source), len(source))
        text, columns = _rendered(source, first, last)
        parts.append(
            Part(
                line=line,
                text=text,
                columns=columns,
                offset=offset,
                end=first + len(source[first:last].rstrip()) + 1,
            )
        )
        offset += len(text) + 1
    return Entry(
        key=command.arg,
        parts=tuple(parts),
        text=" ".join(part.text for part in parts),
    )


def _rendered(source: str, first: int, last: int) -> tuple[str, tuple[int, ...]]:
    """Печатаемый текст участка строки и колонка исходника для каждого знака."""
    hidden = _hidden(source)
    chars: list[str] = []
    columns: list[int] = []
    for index in range(first, last):
        if index in hidden:
            continue
        chars.append(" " if source[index] in _AS_SPACE else source[index])
        columns.append(index + 1)
    return "".join(chars), tuple(columns)


def _hidden(source: str) -> set[int]:
    """Позиции знаков, которых в наборе не видно: имена команд и скобки групп.

    Содержимое групп остаётся: адрес внутри ``\\url`` — часть описания, и
    правила о нём должны его видеть.
    """
    found = {index for index, char in enumerate(source) if char in _INVISIBLE}
    for match in _COMMAND.finditer(source):
        found.update(range(match.start(), match.end()))
    found.update(match.start() for match in _ESCAPE.finditer(source))
    return found
