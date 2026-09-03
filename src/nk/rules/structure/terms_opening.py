"""Вводная фраза перечня терминов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import section_lines, structural_headings

OPENING = "применяют следующие термины"


@rule(
    id="G732-5.5.2-terms-opening",
    clause="5.5.2",
    severity=Severity.ERROR,
    title="Перечень терминов не начинается с установленной фразы",
)
def terms_opening(doc: Document) -> Iterable[Finding]:
    for command, element in structural_headings(doc):
        if element != "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ":
            continue
        body = section_lines(doc, command)
        if any(OPENING in line.stripped.lower() for line in body):
            continue
        yield terms_opening.finding(
            doc,
            command.span,
            message="Перечень терминов не начинается с установленной вводной фразы.",
            requirement=(
                "Перечень терминов и определений начинают со слов о том, что "
                "в настоящем отчёте о НИР применяют следующие термины "
                "с соответствующими определениями."
            ),
            suggestion=(
                "Добавить первой строкой: В настоящем отчёте о НИР применяют следующие "
                "термины с соответствующими определениями."
            ),
            col=command.col,
        )
