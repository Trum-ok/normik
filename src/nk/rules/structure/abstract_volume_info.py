"""Сведения об объёме в реферате."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import section_lines, structural_headings

#: «Отчёт 45 с.», «45 с.,»
VOLUME = re.compile(r"\d+\s*с\.")


@rule(
    id="G732-5.3.2-abstract-volume-info",
    clause="5.3.2",
    severity=Severity.ERROR,
    title="В реферате нет сведений об объёме отчёта",
)
def abstract_volume_info(doc: Document) -> Iterable[Finding]:
    for command, element in structural_headings(doc):
        if element != "РЕФЕРАТ":
            continue
        body = section_lines(doc, command)
        if any(VOLUME.search(line.stripped) for line in body):
            continue
        yield abstract_volume_info.finding(
            doc,
            command.span,
            message="В реферате нет сведений об объёме отчёта.",
            requirement=(
                "Первая компонента реферата — сведения об объёме отчёта, количестве книг, "
                "иллюстраций, таблиц, использованных источников и приложений."
            ),
            suggestion="Добавить строку вида: Отчёт 45 с., 1 кн., 3 рис., 2 табл., 12 источн., 1 прил.",
            col=command.col,
        )
