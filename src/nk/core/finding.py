"""Находка — единица вывода линтера.

Стабильный контракт: на него опираются все правила и все форматы вывода.
Менять состав полей — решение, ломающее JSON-схему.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from nk.core.position import Region

MAX_EXCERPT_LENGTH = 120


class Severity(StrEnum):
    ERROR = "error"
    """Нарушение требования стандарта."""

    WARNING = "warning"
    """Вероятное нарушение либо неоднозначный случай."""

    INFO = "info"
    """Замечание, не влияющее на соответствие."""

    @property
    def rank(self) -> int:
        """Ранг для сравнения: чем меньше, тем серьёзнее."""
        return _SEVERITY_RANK[self]

    def at_least(self, threshold: "Severity") -> bool:
        """Истинно, если уровень не ниже порога — за этим стоит ключ ``--severity``."""
        return self.rank <= threshold.rank


_SEVERITY_RANK: dict[Severity, int] = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}


def truncate_excerpt(text: str, limit: int = MAX_EXCERPT_LENGTH) -> str:
    text = text.rstrip("\n")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


@dataclass(frozen=True, slots=True)
class Fix:
    """Машинная правка: чем заменить фрагмент исходника.

    Отличается от ``suggestion`` тем, что применима без участия человека:
    ``suggestion`` может быть указанием («перенести ниже»), ``Fix`` — всегда
    готовый текст с точными границами.
    """

    region: Region
    replacement: str


@dataclass(frozen=True, slots=True)
class Finding:
    """Одно нарушение: где, что нарушено, что сделать.

    Находка самодостаточна: читающий не обязан открывать ГОСТ или документацию,
    чтобы понять, чего от него хотят.
    """

    rule_id: str
    clause: str
    """Пункт источника требования, например ``6.5.7``; пусто — требование не из стандарта."""

    severity: Severity
    message: str
    """Что не так — одна фраза."""

    requirement: str
    """Что требуется — своими словами, без цитирования ГОСТа."""

    path: Path
    lineno: int
    col: int | None = None
    excerpt: str | None = None
    context: tuple[str, ...] = ()
    """По две строки до и после — для ориентировки."""

    suggestion: str | None = None
    """Конкретное действие для исправления."""

    source: str = ""
    """Источник требования: стандарт профиля либо объявленное им положение.

    Стоит среди полей со значением по умолчанию, а не рядом с ``clause``, потому
    что внутренние диагностики источника не имеют.
    """

    fix: Fix | None = None
    """Правка, применимая ключом ``--fix``. Есть не у всякой находки."""

    @property
    def sort_key(self) -> tuple[str, int, int, str]:
        return (str(self.path), self.lineno, self.col or 0, self.rule_id)
