"""Позиции в исходнике.

Находка указывает на строку — этого хватает человеку. Машинной правке нужны
точные границы: где начинается и где заканчивается заменяемый фрагмент.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True, slots=True)
class Position:
    lineno: int
    """Номер строки, начиная с единицы."""

    col: int
    """Номер колонки, начиная с единицы."""


@dataclass(frozen=True, slots=True)
class Region:
    """Полуинтервал ``[start, end)`` в одном файле.

    Пустой регион (``start == end``) обозначает точку вставки.
    """

    path: Path
    start: Position
    end: Position

    @classmethod
    def in_line(cls, path: Path, lineno: int, start_col: int, end_col: int) -> "Region":
        return cls(path, Position(lineno, start_col), Position(lineno, end_col))

    @classmethod
    def at(cls, path: Path, lineno: int, col: int = 1) -> "Region":
        """Точка вставки перед указанной позицией."""
        point = Position(lineno, col)
        return cls(path, point, point)

    @property
    def is_empty(self) -> bool:
        return self.start == self.end

    def overlaps(self, other: "Region") -> bool:
        if self.path != other.path:
            return False
        if self.is_empty or other.is_empty:
            return self.start == other.start
        return self.start < other.end and other.start < self.end
