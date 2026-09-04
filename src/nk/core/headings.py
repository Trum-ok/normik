"""Команды рубрикации документа.

Заголовок в исходниках не всегда написан ``\\section``: класс ``report`` добавляет
``\\chapter``, а шаблон кафедры заводит под заголовок собственный макрос. Правилам
рубрикации нужна карта команд с уровнем каждой — здесь только модель, разбор
в :mod:`nk.parse.headings`.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

CHAPTER = "chapter"

#: Команды рубрикации и глубина уровня: раздел, подраздел, пункт, подпункт.
#: ``\\chapter`` стоит на уровне раздела; в документе, где главы есть, разбор
#: сдвигает остальные уровни на единицу вниз.
BASE_DEPTH: Mapping[str, int] = {
    "chapter": 1,
    "chapter*": 1,
    "section": 1,
    "section*": 1,
    "subsection": 2,
    "subsection*": 2,
    "subsubsection": 3,
    "subsubsection*": 3,
    "paragraph": 4,
    "paragraph*": 4,
    "subparagraph": 5,
    "subparagraph*": 5,
}

#: Команды, начинающие новую страницу.
PAGE_BREAK_COMMANDS = frozenset({"newpage", "clearpage", "cleardoublepage", "pagebreak"})

#: Уровень команды, которая рубрикацией не является.
NOT_A_HEADING = 0


@dataclass(frozen=True, slots=True)
class Heading:
    """Команда рубрикации: своя или объявленная шаблоном кафедры."""

    name: str
    """Имя команды без обратной косой черты, например ``section*``."""

    depth: int
    numbered: bool
    """Нумеруется ли рубрика: команда без звёздочки."""

    alias_of: str = ""
    """Команда рубрикации, к которой сводится макрос, либо пустая строка."""

    breaks_page: bool = False
    """Начинает ли рубрика новую страницу сама, без ``\\newpage`` перед ней."""


def base_headings(shifted: bool = False) -> dict[str, Heading]:
    """Собственные команды рубрикации LaTeX.

    ``shifted`` — документ разбит на главы, поэтому ``\\section`` в нём подраздел.
    """
    commands: dict[str, Heading] = {}
    for name, depth in BASE_DEPTH.items():
        level = depth + 1 if shifted and not name.startswith(CHAPTER) else depth
        commands[name] = Heading(
            name=name,
            depth=level,
            numbered=not name.endswith("*"),
            breaks_page=name.startswith(CHAPTER),
        )
    return commands


@dataclass(frozen=True, slots=True)
class Headings:
    """Карта команд рубрикации документа."""

    commands: Mapping[str, Heading] = field(default_factory=base_headings)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self.commands)

    def __contains__(self, name: str) -> bool:
        return name in self.commands

    def depth_of(self, name: str) -> int:
        heading = self.commands.get(name)
        return heading.depth if heading is not None else NOT_A_HEADING

    def is_numbered(self, name: str) -> bool:
        heading = self.commands.get(name)
        return heading.numbered if heading is not None else False

    def breaks_page(self, name: str) -> bool:
        """Открывает ли рубрика новую страницу сама: глава либо макрос с разрывом внутри."""
        heading = self.commands.get(name)
        return heading.breaks_page if heading is not None else False

    def alias_of(self, name: str) -> str:
        heading = self.commands.get(name)
        return heading.alias_of if heading is not None else ""
