"""Сведения об объёме в реферате."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import ABSTRACT_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import section_lines, structural_headings

#: «Отчёт 45 с.», «45~с.» — неразрывный пробел ставит сюда правка типографики.
VOLUME = re.compile(r"\d+\s*~?\s*с\.")


@rule(
    id="abstract-volume-info",
    standards={G732: "5.3.2"},
    severity=Severity.ERROR,
    title="В реферате нет сведений об объёме отчёта",
    deprecated_ids=("G732-5.3.2-abstract-volume-info",),
)
def abstract_volume_info(doc: Document) -> Iterable[Finding]:
    """Ищет в реферате сведения об объёме — число со словом «с.», например «45 с.».
    Проверяется только их наличие: сверить число страниц с настоящим объёмом по
    исходникам нельзя.

    ## Почему это нарушение

    Реферат открывается сведениями об объёме отчёта, числе книг, иллюстраций,
    таблиц, использованных источников и приложений. Это первое, по чему читающий
    оценивает работу, и составляется оно по готовому документу.

    ## Как исправить

    Добавить первой строкой реферата строку вида
    «Отчёт 45 с., 1 кн., 3 рис., 2 табл., 12 источн., 1 прил.».
    """
    for command, element in structural_headings(doc):
        if element not in doc.profile.elements.role(ABSTRACT_ROLE):
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
