"""Текст реферата, начатый до перечня ключевых слов."""

from collections.abc import Iterable

from nk.core.document import Document, Line
from nk.core.elements import ABSTRACT
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    KEYWORDS_PREFIX,
    VOLUME_ITEM,
    section_lines,
    structural_headings,
    visible_text,
)


@rule(
    id="G732-6.12.3-abstract-text-position",
    clause="6.12.3",
    severity=Severity.ERROR,
    title="Текст реферата начинается до перечня ключевых слов",
)
def abstract_text_position(doc: Document) -> Iterable[Finding]:
    """Проверяет порядок компонент реферата: сведения об объёме, перечень ключевых
    слов, текст. Находка выдаётся на первый абзац текста, оказавшийся выше перечня
    ключевых слов. Абзац сведений об объёме текстом не считается, строки без
    видимого текста — тоже. Реферат без перечня ключевых слов правило пропускает:
    сравнивать не с чем.

    ## Почему это нарушение

    Текст реферата приводят после ключевых слов, последней из трёх компонент:
    читатель сначала видит объём отчёта и ключевые слова, а потом изложение.

    ## Как исправить

    Перенести абзац ниже перечня ключевых слов.
    """
    for command, element in structural_headings(doc):
        if element != ABSTRACT:
            continue
        lines = section_lines(doc, command)
        keywords = next((line for line in lines if KEYWORDS_PREFIX.match(line.stripped)), None)
        if keywords is None:
            continue
        text = _first_text(lines, keywords)
        if text is None:
            continue
        yield abstract_text_position.finding(
            doc,
            text,
            message=f"Текст реферата начинается выше перечня ключевых слов (строка {keywords.lineno}).",
            requirement=(
                "Текст реферата приводят после сведений об объёме отчёта и перечня ключевых слов."
            ),
            suggestion=f"Перенести абзац ниже строки {keywords.lineno} с перечнем ключевых слов.",
        )


def _first_text(lines: list[Line], keywords: Line) -> Line | None:
    """Первая строка текста реферата выше перечня ключевых слов.

    Сведения об объёме занимают абзац целиком: продолжение переносом строки
    своих «45 с.» не содержит, поэтому пропускается весь абзац, а не строка.
    """
    volume = False
    for line in lines:
        if line.lineno >= keywords.lineno:
            return None
        if line.is_blank:
            volume = False
            continue
        if VOLUME_ITEM.search(line.stripped):
            volume = True
            continue
        if volume or not visible_text(line.stripped).strip():
            continue
        return line
    return None
