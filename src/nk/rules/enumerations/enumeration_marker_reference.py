"""Ссылка на элемент маркированного списка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import (
    LABEL_COMMANDS,
    MARKED_LIST_ENVIRONMENTS,
    referenced_labels,
)


@rule(
    id="enumeration-marker-referenced",
    standards={GR2105: "6.7.4"},
    severity=Severity.ERROR,
    title="На элемент маркированного списка дана ссылка",
    allow_missing_suggestion=True,
)
def enumeration_marker_referenced(doc: Document) -> Iterable[Finding]:
    r"""Ищет метки внутри маркированного списка, на которые в тексте есть `\ref`.
    Метка без ссылки нарушением не является: сослаться ещё не значит сослаться.

    ## Почему это нарушение

    Маркер не даёт элементу обозначения, а сослаться можно только на
    обозначенный элемент: ссылка «см. перечисление» не говорит, на какое.
    Список, элементы которого упоминают в тексте, оформляют буквами или
    номерами со скобкой.

    ## Как исправить

    Заменить маркированный список на буквенный или числовой — в LaTeX это
    `enumerate` с нужным обозначением элементов.
    """
    referenced = referenced_labels(doc)
    for environment in doc.structure.find_environments(*MARKED_LIST_ENVIRONMENTS):
        for command in environment.all_commands():
            if command.name not in LABEL_COMMANDS or command.arg not in referenced:
                continue
            yield enumeration_marker_referenced.finding(
                doc,
                command.span,
                message=f"На элемент маркированного списка ссылаются по метке «{command.arg}».",
                requirement=(
                    "Маркированный список не применяют, если на перечисление приводится ссылка."
                ),
                col=command.col,
            )
