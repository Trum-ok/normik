"""Документ — то, что видит правило.

Два представления одного исходника: построчное для большинства правил
и структурное для случаев, где важна вложенность.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from nk.core.finding import truncate_excerpt
from nk.core.headings import Headings
from nk.core.position import Position, Region
from nk.core.profile import Profile

if TYPE_CHECKING:
    from nk.core.numbering import Numbering

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

    @property
    def length(self) -> int:
        return self.end - self.start + 1


@dataclass(frozen=True, slots=True)
class Command:
    """Команда LaTeX с разобранными аргументами."""

    name: str
    """Имя без обратной косой черты, например ``caption``."""

    path: Path
    lineno: int
    col: int
    options: tuple[str, ...]
    """Содержимое групп в квадратных скобках."""

    args: tuple[str, ...]
    """Содержимое групп в фигурных скобках."""

    span: Span
    region: Region | None = None
    """Точные границы команды вместе с аргументами — основа машинной правки."""

    @property
    def arg(self) -> str:
        return self.args[0] if self.args else ""

    @property
    def start(self) -> Position:
        return Position(self.lineno, self.col)


@dataclass(frozen=True, slots=True)
class Environment:
    """Окружение LaTeX от ``\\begin`` до ``\\end`` включительно."""

    name: str
    path: Path
    span: Span
    options: tuple[str, ...] = ()
    args: tuple[str, ...] = ()
    children: tuple["Environment", ...] = ()
    commands: tuple[Command, ...] = ()
    """Команды непосредственно внутри окружения, без вложенных."""

    def walk(self) -> Iterator["Environment"]:
        """Само окружение и все вложенные, сверху вниз."""
        yield self
        for child in self.children:
            yield from child.walk()

    def all_commands(self) -> Iterator[Command]:
        for env in self.walk():
            yield from env.commands


@dataclass(frozen=True, slots=True)
class Structure:
    """Дерево окружений и команд документа."""

    environments: tuple[Environment, ...] = ()
    """Окружения верхнего уровня."""

    commands: tuple[Command, ...] = ()
    """Команды вне окружений."""

    def walk_environments(self) -> Iterator[Environment]:
        for env in self.environments:
            yield from env.walk()

    def find_environments(self, *names: str) -> Iterator[Environment]:
        wanted = set(names)
        for env in self.walk_environments():
            if not wanted or env.name in wanted:
                yield env

    def find_commands(self, *names: str) -> Iterator[Command]:
        wanted = set(names)
        for command in self._all_commands():
            if not wanted or command.name in wanted:
                yield command

    def enclosing(self, path: Path, lineno: int) -> Environment | None:
        """Самое внутреннее окружение, накрывающее позицию."""
        found: Environment | None = None
        for env in self.walk_environments():
            if not (env.path == path and env.span.contains(lineno)):
                continue
            if found is None or env.span.length <= found.span.length:
                found = env
        return found

    def _all_commands(self) -> Iterator[Command]:
        yield from self.commands
        for env in self.environments:
            yield from env.all_commands()


@dataclass(frozen=True, slots=True)
class Document:
    """Разобранный отчёт: все строки всех файлов плюс действующий профиль."""

    root: Path
    """Каталог или файл, с которого начался обход."""

    files: tuple[Path, ...]
    lines: tuple[Line, ...]
    profile: Profile = field(default_factory=Profile)
    structure: Structure = field(default_factory=Structure)
    numbering: "Numbering" = field(default_factory=lambda: _empty_numbering())
    headings: Headings = field(default_factory=Headings)
    """Команды рубрикации отчёта, включая макросы шаблона кафедры."""

    _index: dict[Path, tuple[Line, ...]] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _order: dict[Path, int] = field(init=False, repr=False, compare=False, default_factory=dict)

    def __post_init__(self) -> None:
        by_file: dict[Path, list[Line]] = {}
        for line in self.lines:
            by_file.setdefault(line.path, []).append(line)
        # Мутация словаря допустима и на frozen-датаклассе: атрибут не переприсваивается.
        self._index.update({path: tuple(items) for path, items in by_file.items()})
        self._order.update({path: index for index, path in enumerate(self.files)})

    def file_index(self, path: Path) -> int:
        """Место файла в порядке разворачивания включений.

        По нему упорядочивают находки и заголовки: алфавит имён файлов порядку
        отчёта не соответствует.
        """
        return self._order.get(path, len(self.files))

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

    def slice(self, region: Region) -> str:
        """Исходный текст под регионом — основа правок, меняющих фрагмент точечно."""
        lines = self.lines_of(region.path)
        if not lines:
            return ""
        first, last = region.start.lineno, region.end.lineno
        if not (1 <= first <= len(lines) and 1 <= last <= len(lines)):
            return ""
        if first == last:
            return lines[first - 1].raw[region.start.col - 1 : region.end.col - 1]
        parts = [lines[first - 1].raw[region.start.col - 1 :]]
        parts.extend(line.raw for line in lines[first : last - 1])
        parts.append(lines[last - 1].raw[: region.end.col - 1])
        return "\n".join(parts)

    def context(self, path: Path, lineno: int, radius: int = CONTEXT_RADIUS) -> tuple[str, ...]:
        """Соседние строки вокруг позиции, включая саму строку нарушения."""
        lines = self.lines_of(path)
        start = max(1, lineno - radius)
        end = min(len(lines), lineno + radius)
        if start > end:
            return ()
        return tuple(truncate_excerpt(item.raw) for item in lines[start - 1 : end])


def _empty_numbering() -> "Numbering":
    # Импорт отложен: модель нумерации опирается на Span из этого модуля.
    from nk.core.numbering import Numbering

    return Numbering()
