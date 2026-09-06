"""Ссылка на отсутствующую запись списка источников."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import (
    BIBITEM_COMMAND,
    BIBLIOGRAPHY_ENVIRONMENT,
    CITE_COMMANDS,
    ordered_commands,
)


@rule(
    id="cite-unresolved",
    standards={G732: "6.9.1", GR2105: "6.4.2"},
    severity=Severity.ERROR,
    title="Ссылка указывает на отсутствующую запись списка источников",
    deprecated_ids=("G732-6.9.1-cite-unresolved",),
)
def cite_unresolved(doc: Document) -> Iterable[Finding]:
    r"""Проверяет, что каждый ключ ссылки на источник объявлен записью `\bibitem`
    в списке. Работает только когда список набран в исходнике: у собираемого
    BibTeX списка ключи известны лишь после сборки.

    ## Почему это нарушение

    Номер библиографического описания в списке соответствует номеру ссылки.
    Неразрешённая ссылка печатается в документе как «[?]» и номера не получает.

    ## Как исправить

    Добавить запись в список источников либо исправить ключ в ссылке.
    """
    bibliographies = list(doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT))
    if not bibliographies:
        return

    known = {
        command.arg
        for bibliography in bibliographies
        for command in bibliography.all_commands()
        if command.name == BIBITEM_COMMAND and command.arg
    }
    for command in ordered_commands(doc, *CITE_COMMANDS):
        missing = [
            key.strip()
            for arg in command.args
            for key in arg.split(",")
            if key.strip() and key.strip() not in known
        ]
        if not missing:
            continue
        listed = ", ".join(repr(key) for key in missing)
        yield cite_unresolved.finding(
            doc,
            command.span,
            message=f"Ссылка на источник {listed}: такой записи в списке нет.",
            requirement=(
                "Порядковый номер библиографического описания в списке источников "
                "соответствует номеру ссылки."
            ),
            suggestion=f"Добавить \\bibitem{{{missing[0]}}} в список источников либо исправить ключ.",
            col=command.col,
        )
