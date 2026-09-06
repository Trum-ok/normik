"""Вводная фраза перечня сокращений."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import ABBREVIATIONS_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import section_lines, structural_headings

OPENING = "применяют следующие сокращения"


@rule(
    id="abbreviations-opening",
    standards={G732: "5.6.1", GR2105: "6.1.2"},
    severity=Severity.ERROR,
    title="Перечень сокращений не начинается с установленной фразы",
    deprecated_ids=("G732-5.6.1-abbreviations-opening",),
)
def abbreviations_opening(doc: Document) -> Iterable[Finding]:
    """Ищет в теле перечня сокращений и обозначений вводную фразу — строку со словами
    «применяют следующие сокращения», без учёта регистра. Если её нет, элемент
    считается открытым неверно.

    ## Почему это нарушение

    У перечня сокращений фиксированный зачин: он оговаривает, что перечисленные
    обозначения действуют в пределах этого отчёта, а не приводятся справочно.
    Без него элемент читается как произвольный список.

    ## Как исправить

    Поставить первой строкой после заголовка фразу «В настоящем отчёте о НИР
    применяют следующие сокращения и обозначения.», а сам перечень — ниже.
    """
    for command, element in structural_headings(doc):
        if element not in doc.profile.elements.role(ABBREVIATIONS_ROLE):
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
