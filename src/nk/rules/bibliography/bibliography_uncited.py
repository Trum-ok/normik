"""Запись списка источников, на которую нет ссылок."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import BIBITEM_COMMAND, BIBLIOGRAPHY_ENVIRONMENT, cited_keys


@rule(
    id="bibitem-uncited",
    standards={G732: "6.16", GR2105: "6.4.2"},
    severity=Severity.WARNING,
    title="На запись списка источников нет ссылок в тексте",
    deprecated_ids=("G732-6.16-bibitem-uncited",),
)
def bibitem_uncited(doc: Document) -> Iterable[Finding]:
    """Ищет записи списка источников, на которые в тексте нет ни одной ссылки.

    ## Почему это нарушение

    Список содержит источники, использованные при составлении отчёта. Запись,
    на которую нет ссылки, использованной не является и к тому же ломает
    нумерацию по порядку упоминания.

    ## Как исправить

    Сослаться на источник в тексте либо убрать запись из списка.
    """
    cited = cited_keys(doc)
    for bibliography in doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT):
        for command in bibliography.all_commands():
            if command.name != BIBITEM_COMMAND or not command.arg:
                continue
            if command.arg in cited:
                continue
            yield bibitem_uncited.finding(
                doc,
                command.span,
                message=f"На запись {command.arg!r} в тексте нет ни одной ссылки.",
                requirement=(
                    "Список содержит источники, использованные при составлении отчёта; "
                    "сведения располагают в порядке появления ссылок на них."
                ),
                suggestion=f"Сослаться на источник \\cite{{{command.arg}}} либо убрать запись.",
                col=command.col,
            )
