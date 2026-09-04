"""Разметка математики в исходнике.

Формулы задаются двумя способами: окружениями (``equation``, ``align``) и парными
разделителями (``$…$``, ``$$…$$``, ``\\(…\\)``, ``\\[…\\]``). Разделители открываются
и закрываются в разных строках, поэтому разбор идёт автоматом по файлу целиком,
а не построчно.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from nk.core.document import Document, Line
from nk.core.math import MATH_ENVIRONMENTS, Interval, Math
from nk.parse.structure import VERBATIM_ENVIRONMENTS

#: Парные разделители: чем формула открывается и чем закрывается.
DELIMITERS: dict[str, str] = {"$$": "$$", "$": "$", "\\(": "\\)", "\\[": "\\]"}

_OPENINGS = ("$$", "$", "\\(", "\\[")


@dataclass
class _Open:
    """Начатая формула: чем закрывается и где началась."""

    closing: str
    lineno: int
    col: int


def build_math(doc: Document) -> Math:
    """Разметить математику по всем файлам отчёта."""
    # Доллар в листинге — знак оболочки, а не начало формулы: приняв его за
    # формулу, разбор проглотил бы весь дальнейший текст файла.
    verbatim = doc.structure.covered_lines(*VERBATIM_ENVIRONMENTS)
    intervals: dict[tuple[Path, int], list[Interval]] = {}
    for path in doc.files:
        for key, found in _scan_file(path, doc.lines_of(path), verbatim).items():
            intervals.setdefault(key, []).extend(found)

    for environment in doc.structure.find_environments(*MATH_ENVIRONMENTS):
        for lineno in range(environment.span.start, environment.span.end + 1):
            line = doc.line_at(environment.path, lineno)
            if line is not None:
                intervals.setdefault((environment.path, lineno), []).append((1, len(line.raw) + 1))

    return Math({key: tuple(sorted(found)) for key, found in intervals.items()})


def _scan_file(
    path: Path, lines: Sequence[Line], verbatim: frozenset[tuple[Path, int]]
) -> dict[tuple[Path, int], list[Interval]]:
    """Участки формул, заданных парными разделителями."""
    intervals: dict[tuple[Path, int], list[Interval]] = {}
    opened: _Open | None = None

    for line in lines:
        if (path, line.lineno) in verbatim:
            continue
        text = line.stripped
        index = 0
        while index < len(text):
            if text[index] == "\\" and index + 1 < len(text) and text[index + 1] not in "([)]$":
                # Экранированный знак и любая другая команда: два знака за раз, чтобы
                # \\ перед [ не был принят за начало выключной формулы.
                index += 2
                continue
            if text[index] == "\\" and index + 1 < len(text) and text[index + 1] == "$":
                index += 2
                continue

            token = _token_at(text, index, opened)
            if token is None:
                index += 1
                continue

            if opened is None:
                opened = _Open(closing=DELIMITERS[token], lineno=line.lineno, col=index + 1)
            else:
                _add(intervals, path, opened, line.lineno, index + len(token) + 1, lines)
                opened = None
            index += len(token)

    if opened is not None and lines:
        last = lines[-1]
        _add(intervals, path, opened, last.lineno, len(last.raw) + 1, lines)
    return intervals


def _token_at(text: str, index: int, opened: _Open | None) -> str | None:
    """Разделитель в этой позиции: ожидаемый закрывающий либо любой открывающий."""
    if opened is not None:
        return opened.closing if text.startswith(opened.closing, index) else None
    for opening in _OPENINGS:
        if text.startswith(opening, index):
            return opening
    return None


def _add(
    intervals: dict[tuple[Path, int], list[Interval]],
    path: Path,
    opened: _Open,
    end_lineno: int,
    end_col: int,
    lines: Sequence[Line],
) -> None:
    """Отметить формулу от места открытия до места закрытия, строка за строкой."""
    for line in lines:
        if not (opened.lineno <= line.lineno <= end_lineno):
            continue
        start = opened.col if line.lineno == opened.lineno else 1
        end = end_col if line.lineno == end_lineno else len(line.raw) + 1
        intervals.setdefault((path, line.lineno), []).append((start, end))
