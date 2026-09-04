"""Структурные элементы отчёта.

Наименования элементов — общий словарь для доброго десятка правил: состав,
порядок, регистр заголовков, содержание реферата. Кафедра может называть элемент
иначе, чем стандарт, поэтому наименование приводится к каноническому с учётом
синонимов из профиля.
"""

from collections.abc import Mapping

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

#: Наименования структурных элементов отчёта по разделу 4 стандарта.
STRUCTURAL_ELEMENTS = frozenset(
    {
        CONTRIBUTORS,
        ABSTRACT,
        CONTENTS,
        TERMS,
        ABBREVIATIONS,
        DEFINITIONS,
        INTRODUCTION,
        CONCLUSION,
        BIBLIOGRAPHY,
        APPENDIX,
    }
)

#: Элементы, где ведут перечень терминов.
TERMS_ELEMENTS = frozenset({TERMS})

#: Элементы, где ведут перечень сокращений: свой либо объединённый.
ABBREVIATION_ELEMENTS = frozenset({ABBREVIATIONS, DEFINITIONS})

#: Элементы, содержимое которых — перечень записей через тире.
LISTING_ELEMENTS = TERMS_ELEMENTS | ABBREVIATION_ELEMENTS

#: Порядок структурных элементов по разделу 4. Термины и объединённый перечень
#: занимают одно место, поэтому ранг у них общий.
ELEMENT_ORDER: dict[str, int] = {
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
}


def normalize_element(text: str) -> str:
    """Наименование без знаков препинания и различий в регистре."""
    return " ".join(text.upper().replace(",", " ").replace(".", " ").split())


def canonical_element(normalized: str, aliases: Mapping[str, str]) -> str | None:
    """Каноническое наименование элемента либо ``None``.

    ``aliases`` — синонимы кафедры из профиля: ключи уже нормализованы.
    """
    name = aliases.get(normalized, normalized)
    if name in STRUCTURAL_ELEMENTS:
        return name
    if name.startswith(f"{APPENDIX} "):
        return APPENDIX
    return None
