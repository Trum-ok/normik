"""Документ — то, что видит правило.

Два представления одного исходника: построчное для большинства правил
и структурное для случаев, где важна вложенность.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from nk.core.finding import truncate_excerpt
from nk.core.profile import Profile

CONTEXT_RADIUS = 2


@dataclass(frozen=True, slots=True)
class Line:
    """Строка исходника с сохранением позиции в конкретном файле."""

    path: Path
    lineno: int
    """Номер строки, начиная с единицы."""

    raw: str
    stripped: str
    """Строка с вырезанным комментарием (``%`` с учётом экранированного ``\\%``)."""

    @property
    def is_blank(self) -> bool:
        return not self.stripped.strip()


@dataclass(frozen=True, slots=True)
class Span:
    """Диапазон строк в одном файле, включая обе границы."""

    path: Path
    start: int
    end: int

    def contains(self, lineno: int) -> bool:
        return self.start <= lineno <= self.end


@dataclass(frozen=True, slots=True)
class Document:
    """Разобранный отчёт: все строки всех файлов плюс действующий профиль."""

    root: Path
    """Каталог или файл, с которого начался обход."""

    files: tuple[Path, ...]
    lines: tuple[Line, ...]
    profile: Profile = field(default_factory=Profile)

    _index: dict[Path, tuple[Line, ...]] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        by_file: dict[Path, list[Line]] = {}
        for line in self.lines:
            by_file.setdefault(line.path, []).append(line)
        # Мутация словаря допустима и на frozen-датаклассе: атрибут не переприсваивается.
        self._index.update({path: tuple(items) for path, items in by_file.items()})

    def lines_of(self, path: Path) -> tuple[Line, ...]:
        return self._index.get(path, ())

    def line_at(self, path: Path, lineno: int) -> Line | None:
        lines = self.lines_of(path)
        if 1 <= lineno <= len(lines):
            return lines[lineno - 1]
        return None

    def iter_lines(self) -> Iterator[Line]:
        yield from self.lines

    def excerpt(self, path: Path, lineno: int) -> str | None:
        line = self.line_at(path, lineno)
        return truncate_excerpt(line.raw) if line is not None else None

    def context(self, path: Path, lineno: int, radius: int = CONTEXT_RADIUS) -> tuple[str, ...]:
        """Соседние строки вокруг позиции, включая саму строку нарушения."""
        lines = self.lines_of(path)
        start = max(1, lineno - radius)
        end = min(len(lines), lineno + radius)
        if start > end:
            return ()
        return tuple(truncate_excerpt(item.raw) for item in lines[start - 1 : end])
