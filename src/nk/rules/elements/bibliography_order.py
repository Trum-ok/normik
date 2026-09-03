"""Порядок записей в списке источников."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    BIBITEM_COMMAND,
    BIBLIOGRAPHY_ENVIRONMENT,
    CITE_COMMANDS,
    ordered_commands,
)


@rule(
    id="G732-6.16-bibliography-order",
    clause="6.16",
    severity=Severity.ERROR,
    title="Записи списка источников идут не в порядке появления ссылок",
)
def bibliography_order(doc: Document) -> Iterable[Finding]:
    first_citation: dict[str, int] = {}
    for position, command in enumerate(ordered_commands(doc, *CITE_COMMANDS)):
        for arg in command.args:
            for key in arg.split(","):
                first_citation.setdefault(key.strip(), position)

    for bibliography in doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT):
        previous_key = ""
        previous_position = -1
        for command in sorted(bibliography.all_commands(), key=lambda item: item.lineno):
            if command.name != BIBITEM_COMMAND or not command.arg:
                continue
            position = first_citation.get(command.arg)
            if position is None:
                continue
            if position >= previous_position:
                previous_key, previous_position = command.arg, position
                continue
            yield bibliography_order.finding(
                doc,
                command.span,
                message=(
                    f"Запись {command.arg!r} процитирована раньше, чем {previous_key!r}, "
                    "но стоит в списке позже."
                ),
                requirement=(
                    "Сведения об источниках располагают в порядке появления ссылок "
                    "на них в тексте отчёта."
                ),
                suggestion=f"Переставить \\bibitem{{{command.arg}}} выше \\bibitem{{{previous_key}}}.",
                col=command.col,
            )
            previous_key, previous_position = command.arg, position
