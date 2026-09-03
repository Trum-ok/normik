"""Вводная фраза перечня сокращений."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import section_lines, structural_headings

OPENING = "применяют следующие сокращения"
ELEMENTS = frozenset({"ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ", "ОПРЕДЕЛЕНИЯ ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ"})


@rule(
    id="G732-5.6.1-abbreviations-opening",
    clause="5.6.1",
    severity=Severity.ERROR,
    title="Перечень сокращений не начинается с установленной фразы",
)
def abbreviations_opening(doc: Document) -> Iterable[Finding]:
    for command, element in structural_headings(doc):
        if element not in ELEMENTS:
            continue
        body = section_lines(doc, command)
        if any(OPENING in line.stripped.lower() for line in body):
            continue
        yield abbreviations_opening.finding(
            doc,
            command.span,
            message="Перечень сокращений не начинается с установленной вводной фразы.",
            requirement=(
                "Перечень сокращений и обозначений начинают со слов о том, что "
                "в настоящем отчёте о НИР применяют следующие сокращения и обозначения."
            ),
            suggestion=(
                "Добавить первой строкой: В настоящем отчёте о НИР применяют следующие "
                "сокращения и обозначения."
            ),
            col=command.col,
        )
