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


#: Знак на месте отброшенного куска строки.
ELLIPSIS = "…"

#: Сколько знаков оставить слева от места нарушения, когда начало строки отброшено.
LEAD = 40


def truncate_excerpt(text: str, limit: int = MAX_EXCERPT_LENGTH) -> str:
    """Начало строки в пределах длины: остаток отбрасывается."""
    return excerpt_window(text, None, limit)[0]


def excerpt_window(text: str, col: int | None, limit: int = MAX_EXCERPT_LENGTH) -> tuple[str, int]:
    """Кусок строки, в который попадает место нарушения, и сколько знаков отброшено слева.

    Длинную строку нельзя резать с начала: нарушение на двухсотом знаке иначе
    не попадает в вывод вовсе, и находка перестаёт быть самодостаточной.
    Поэтому окно сдвигается к месту нарушения, оставляя перед ним немного
    текста для опоры.
    """
    text = text.rstrip("\n")
    if len(text) <= limit:
        return text, 0
    if col is None or col <= limit:
        return text[: limit - 1] + ELLIPSIS, 0

    # Окно упирается в конец строки: там хвост показывают целиком, и место
    # под завершающий знак сокращения освобождается под сам текст.
    start = min(col - 1 - LEAD, len(text) - limit + 1)
    if start + limit - 1 >= len(text):
        return ELLIPSIS + text[start:], start - 1
    return ELLIPSIS + text[start : start + limit - 2] + ELLIPSIS, start - 1


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

    excerpt_offset: int = 0
    """Сколько знаков отброшено слева от строки нарушения при её сокращении.

    Позиция ``col`` считается по исходной строке, а показывается окно вокруг
    неё: без смещения указатель встал бы не под тот знак.
    """

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
