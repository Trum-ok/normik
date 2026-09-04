"""Порядок записей, собираемых BibTeX."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import BIBLIOGRAPHY_ENVIRONMENT, BIBTEX_COMMANDS, ordered_commands


@rule(
    id="G732-6.16-bibtex-order-unverifiable",
    clause="6.16",
    severity=Severity.INFO,
    title="Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется",
)
def bibtex_order_unverifiable(doc: Document) -> Iterable[Finding]:
    """Сообщает, что список источников собирается BibTeX: порядок записей задаёт
    стиль оформления, и по исходникам он не проверяется. Находка выдаётся один
    раз на документ и только если списка в исходнике нет.

    ## Почему это нарушение

    Это не нарушение, а граница применимости инструмента: порядок появления
    ссылок обеспечивается выбором стиля, а проверить его можно лишь по
    собранному документу.

    ## Как исправить

    Убедиться, что выбран стиль с порядком по появлению ссылок — например
    `unsrt`. Если порядок проверяется другим способом, правило отключается
    профилем.
    """
    if any(doc.structure.find_environments(BIBLIOGRAPHY_ENVIRONMENT)):
        return
    for command in ordered_commands(doc, *BIBTEX_COMMANDS):
        yield bibtex_order_unverifiable.finding(
            doc,
            command.span,
            message="Библиография собирается BibTeX: порядок записей задаёт стиль, а не исходник.",
            requirement=(
                "Сведения об источниках располагают в порядке появления ссылок "
                "на них в тексте отчёта."
            ),
            suggestion="Убедиться, что выбран стиль с порядком появления ссылок, например unsrt.",
            col=command.col,
        )
        return
