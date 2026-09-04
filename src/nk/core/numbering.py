"""Нумерация плавающих объектов.

Номер рисунка, таблицы и формулы в исходнике не написан: его формирует класс
документа. Чтобы проверять требования к нумерации и называть объект так, как
его увидит читатель, счётчики приходится воспроизводить.

Разбор — в :mod:`nk.parse.numbering`; здесь только модель.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from nk.core.document import Span

FIGURE = "figure"
TABLE = "table"
EQUATION = "equation"

#: Как выглядит объект в тексте: «Рисунок», «Таблица», «формула».
KIND_NAMES: dict[str, str] = {
    FIGURE: "Рисунок",
    TABLE: "Таблица",
    EQUATION: "Формула",
}


class Scheme(StrEnum):
    CONTINUOUS = "continuous"
    """Сквозная нумерация в пределах всего отчёта."""

    BY_SECTION = "by_section"
    """Нумерация в пределах раздела: номер раздела и порядковый номер через точку."""


@dataclass(frozen=True, slots=True)
class Numbered:
    """Плавающий объект с номером, который увидит читатель."""

    kind: str
    span: Span
    number: str
    scheme: Scheme
    appendix: str = ""
    """Обозначение приложения, внутри которого находится объект, либо пустая строка."""

    @property
    def in_appendix(self) -> bool:
        return bool(self.appendix)

    @property
    def title(self) -> str:
        return f"{KIND_NAMES.get(self.kind, self.kind)} {self.number}"


@dataclass(frozen=True, slots=True)
class SchemeChange:
    """Место, где схема нумерации задана явно."""

    kind: str
    path: Path
    lineno: int
    col: int
    scheme: Scheme


@dataclass(frozen=True, slots=True)
class Numbering:
    items: tuple[Numbered, ...] = ()
    changes: tuple[SchemeChange, ...] = ()

    def by_kind(self, kind: str) -> tuple[Numbered, ...]:
        return tuple(item for item in self.items if item.kind == kind)

    def changes_of(self, kind: str) -> tuple[SchemeChange, ...]:
        return tuple(change for change in self.changes if change.kind == kind)
