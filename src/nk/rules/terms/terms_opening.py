"""Вводная фраза перечня терминов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import TERMS_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import section_lines, structural_headings

OPENING = "применяют следующие термины"


@rule(
    id="terms-opening",
    standards={G732: "5.5.2"},
    severity=Severity.ERROR,
    title="Перечень терминов не начинается с установленной фразы",
    deprecated_ids=("G732-5.5.2-terms-opening",),
)
def terms_opening(doc: Document) -> Iterable[Finding]:
    """Ищет в теле перечня терминов и определений вводную фразу — строку со словами
    «применяют следующие термины», без учёта регистра.

    ## Почему это нарушение

    Перечень терминов открывается фразой, оговаривающей, что определения действуют
    в пределах этого отчёта. Определения без такой оговорки читаются как претензия
    на общеупотребительность.

    ## Как исправить

    Поставить первой строкой после заголовка фразу «В настоящем отчёте о НИР
    применяют следующие термины с соответствующими определениями.».
    """
    for command, element in structural_headings(doc):
        if element not in doc.profile.elements.role(TERMS_ROLE):
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
