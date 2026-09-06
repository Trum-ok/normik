"""Источники требований.

Правило проверяет требование, а не стандарт: одно и то же требование к подписи
рисунка записано и в ГОСТ 7.32-2017, и в ГОСТ Р 2.105-2019, только под разными
пунктами. Поэтому правило объявляет карту «стандарт — пункт», а какой из них
попадёт в находку, решает профиль.

Пункт может задать и профиль: положение вуза — тоже источник требований, со
своей нумерацией. Такой источник объявляется в самом профиле, см.
:mod:`nk.core.profile`.
"""

from dataclasses import dataclass


class UnknownStandardError(ValueError):
    """Профиль назвал стандарт, которого нет."""


@dataclass(frozen=True, slots=True)
class Standard:
    id: str
    """Короткое имя: им профиль называет активный стандарт, им же правило ключует пункты."""

    title: str
    """Как стандарт называется в находке и в документации."""


G732 = Standard("G732", "ГОСТ 7.32-2017")
GR2105 = Standard("GR2105", "ГОСТ Р 2.105-2019")

STANDARDS: dict[str, Standard] = {item.id: item for item in (G732, GR2105)}

#: Стандарт, по которому проверяется отчёт, пока профиль не сказал иначе.
DEFAULT = G732

#: Пункта нет: требование не из стандарта — типографика, внутренние диагностики.
NO_CLAUSE = ""


def get(standard_id: str) -> Standard:
    try:
        return STANDARDS[standard_id]
    except KeyError:
        allowed = ", ".join(sorted(STANDARDS))
        raise UnknownStandardError(
            f"неизвестный стандарт {standard_id!r}, допустимы: {allowed}"
        ) from None
