"""Математика в исходнике.

Формула — не проза: дефис в ней знак вычитания, кавычки — штрихи, пробел перед
единицей ставит сам TeX. Правила типографики обязаны видеть текст без формул,
поэтому границы математики размечаются один раз при разборе.

Разметка — в :mod:`nk.parse.math`; здесь только модель.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

#: Окружения выключных формул.
MATH_ENVIRONMENTS = frozenset(
    {
        "equation",
        "equation*",
        "align",
        "align*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "displaymath",
        "eqnarray",
        "eqnarray*",
        "alignat",
        "alignat*",
        "flalign",
        "flalign*",
    }
)

#: Интервал колонок ``[start, end)``, считая от единицы.
Interval = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Math:
    """Участки математики по строкам файлов."""

    intervals: Mapping[tuple[Path, int], tuple[Interval, ...]] = field(default_factory=dict)

    def of_line(self, path: Path, lineno: int) -> tuple[Interval, ...]:
        return self.intervals.get((path, lineno), ())

    def covers(self, path: Path, lineno: int, col: int) -> bool:
        return any(start <= col < end for start, end in self.of_line(path, lineno))

    def mask(self, path: Path, lineno: int, text: str) -> str:
        """Строка, где математика заменена пробелами.

        Позиции находок считаются по исходной строке, поэтому длина сохраняется.
        """
        intervals = self.of_line(path, lineno)
        if not intervals:
            return text
        chars = list(text)
        for start, end in intervals:
            for index in range(max(start, 1) - 1, min(end - 1, len(chars))):
                chars[index] = " "
        return "".join(chars)
