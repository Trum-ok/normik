"""Структурные элементы отчёта.

Наименования элементов — общий словарь для доброго десятка правил: состав,
порядок, регистр заголовков, содержание реферата. Словарь принадлежит профилю,
а не ядру: у разных источников требований расходятся и состав элементов, и их
порядок, и сами наименования. Значения по умолчанию — по разделу 4 стандарта.

Правило спрашивает у словаря не наименование, а роль: не «это РЕФЕРАТ?»,
а «это элемент, где ведут реферат?». Наименование под ролью задаёт профиль.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

CONTRIBUTORS = "СПИСОК ИСПОЛНИТЕЛЕЙ"
ABSTRACT = "РЕФЕРАТ"
CONTENTS = "СОДЕРЖАНИЕ"
TERMS = "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"
ABBREVIATIONS = "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ"
DEFINITIONS = "ОПРЕДЕЛЕНИЯ ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ"
"""Объединённый перечень: стандарт допускает его вместо двух отдельных."""

INTRODUCTION = "ВВЕДЕНИЕ"
CONCLUSION = "ЗАКЛЮЧЕНИЕ"
BIBLIOGRAPHY = "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"
APPENDIX = "ПРИЛОЖЕНИЕ"

ABSTRACT_ROLE = "abstract"
CONTENTS_ROLE = "contents"
TERMS_ROLE = "terms"
ABBREVIATIONS_ROLE = "abbreviations"
BIBLIOGRAPHY_ROLE = "bibliography"
APPENDIX_ROLE = "appendix"

LISTING_ROLE = "listing"
"""Роль, собираемая из двух других: перечни терминов и сокращений устроены одинаково."""

#: Роли, которые профиль задаёт сам. Производные сюда не входят.
ROLES = frozenset(
    {
        ABSTRACT_ROLE,
        CONTENTS_ROLE,
        TERMS_ROLE,
        ABBREVIATIONS_ROLE,
        BIBLIOGRAPHY_ROLE,
        APPENDIX_ROLE,
    }
)


class ElementsError(ValueError):
    """Словарь элементов не согласован сам с собой."""


def normalize_element(text: str) -> str:
    """Наименование без знаков препинания и различий в регистре."""
    return " ".join(text.upper().replace(",", " ").replace(".", " ").split())


@dataclass(frozen=True, slots=True)
class Elements:
    """Словарь структурных элементов: состав, порядок, роли и синонимы.

    Состав задаёт :attr:`order`: наименования, которого в нём нет, словарь не знает,
    и заголовок с ним структурным элементом не считается.
    """

    order: Mapping[str, int]
    """Наименование и его ранг. Элементы с общим рангом взаимозаменяемы по месту."""

    roles: Mapping[str, frozenset[str]]
    """Роль и наименования, которые её исполняют."""

    aliases: Mapping[str, str] = field(default_factory=dict)
    """Наименования кафедры и канонические наименования источника; ключи нормализованы."""

    def __post_init__(self) -> None:
        unknown = {name for names in self.roles.values() for name in names} - self.order.keys()
        if unknown:
            raise ElementsError(f"роль ссылается на элементы вне состава: {sorted(unknown)}")

    @property
    def names(self) -> frozenset[str]:
        """Все известные словарю наименования."""
        return frozenset(self.order)

    def rank(self, name: str) -> int:
        return self.order[name]

    def ordered(self) -> tuple[tuple[str, ...], ...]:
        """Наименования по местам, в установленном порядке — для формулировок находок.

        Одно место занимают несколько наименований, если они взаимозаменяемы.
        """
        places: dict[int, list[str]] = {}
        for name in sorted(self.order):
            places.setdefault(self.order[name], []).append(name)
        return tuple(tuple(places[rank]) for rank in sorted(places))

    def role(self, role: str) -> frozenset[str]:
        """Наименования, исполняющие роль. Незанятая роль — пустое множество."""
        if role == LISTING_ROLE:
            return self.role(TERMS_ROLE) | self.role(ABBREVIATIONS_ROLE)
        return self.roles.get(role, frozenset())

    def canonical(self, normalized: str) -> str | None:
        """Каноническое наименование элемента по нормализованному заголовку либо ``None``.

        Приложение опознаётся и по обозначению после наименования: «ПРИЛОЖЕНИЕ А».
        """
        name = self.aliases.get(normalized, normalized)
        if name in self.order:
            return name
        for appendix in self.role(APPENDIX_ROLE):
            if name.startswith(f"{appendix} "):
                return appendix
        return None


#: Состав и порядок по разделу 4 стандарта. Термины и объединённый перечень
#: занимают одно место, поэтому ранг у них общий.
DEFAULT_ELEMENTS = Elements(
    order={
        CONTRIBUTORS: 1,
        ABSTRACT: 2,
        CONTENTS: 3,
        TERMS: 4,
        DEFINITIONS: 4,
        ABBREVIATIONS: 5,
        INTRODUCTION: 6,
        CONCLUSION: 7,
        BIBLIOGRAPHY: 8,
        APPENDIX: 9,
    },
    roles={
        ABSTRACT_ROLE: frozenset({ABSTRACT}),
        CONTENTS_ROLE: frozenset({CONTENTS}),
        TERMS_ROLE: frozenset({TERMS}),
        ABBREVIATIONS_ROLE: frozenset({ABBREVIATIONS, DEFINITIONS}),
        BIBLIOGRAPHY_ROLE: frozenset({BIBLIOGRAPHY}),
        APPENDIX_ROLE: frozenset({APPENDIX}),
    },
)
