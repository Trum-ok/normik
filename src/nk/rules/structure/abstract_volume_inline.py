"""Сведения об объёме реферата, оформленные не в строку."""

from collections.abc import Iterable
from itertools import pairwise

from nk.core.document import Document, Line
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import VOLUME_ITEM, section_lines, structural_headings

LIST_ENVIRONMENTS = frozenset({"itemize", "enumerate", "description"})
LINE_BREAK = "\\\\"


@rule(
    id="G732-6.12.1-abstract-volume-inline",
    clause="6.12.1",
    severity=Severity.ERROR,
    title="Сведения об объёме реферата приведены не в строку",
)
def abstract_volume_inline(doc: Document) -> Iterable[Finding]:
    """Проверяет, что первая компонента реферата — одна строка через запятые.

    ## Почему это нарушение

    Сведения об объёме отчёта, количестве книг, иллюстраций, таблиц, источников
    и приложений располагают с абзацного отступа в строку через запятые.
    Список или разбивка по абзацам стандартом не предусмотрены.

    ## Как исправить

    Свести перечисление в одну строку: `Отчёт 45 с., 1 кн., 3 рис., 2 табл.,
    12 источн., 1 прил.`
    """
    for command, element in structural_headings(doc):
        if element != "РЕФЕРАТ":
            continue
        items = [line for line in section_lines(doc, command) if VOLUME_ITEM.search(line.stripped)]
        if not items:
            continue
        yield from _report(doc, items)


def _report(doc: Document, items: list[Line]) -> Iterable[Finding]:
    for line in items:
        environment = doc.structure.enclosing(line.path, line.lineno)
        if environment is not None and environment.name in LIST_ENVIRONMENTS:
            yield abstract_volume_inline.finding(
                doc,
                line,
                message=f"Сведения об объёме оформлены списком {environment.name}.",
                requirement=(
                    "Сведения об объёме приводят с абзацного отступа в строку через запятые."
                ),
                suggestion="Убрать список и записать перечисление одной строкой через запятые.",
            )
            return
        if LINE_BREAK in line.stripped:
            yield abstract_volume_inline.finding(
                doc,
                line,
                message="Сведения об объёме разорваны принудительным переносом строки.",
                requirement=(
                    "Сведения об объёме приводят с абзацного отступа в строку через запятые."
                ),
                suggestion="Убрать «\\\\» и записать перечисление одной строкой через запятые.",
            )
            return

    separated = _split_by_paragraph(doc, items)
    if separated is not None:
        yield abstract_volume_inline.finding(
            doc,
            separated,
            message="Сведения об объёме разбиты на несколько абзацев.",
            requirement="Сведения об объёме приводят с абзацного отступа в строку через запятые.",
            suggestion="Свести перечисление в один абзац через запятые.",
        )


def _split_by_paragraph(doc: Document, items: list[Line]) -> Line | None:
    """Первый элемент, отделённый от предыдущего пустой строкой."""
    for previous, current in pairwise(items):
        gap = range(previous.lineno + 1, current.lineno)
        if any((doc.line_at(current.path, lineno) or previous).is_blank for lineno in gap):
            return current
    return None
