"""Ссылка в тексте на каждый рисунок."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, labels, referenced_labels

REQUIREMENT = "На все иллюстрации в отчёте должны быть даны ссылки со словом «рисунок» и номером."


@rule(
    id="G732-6.5.1-figure-no-reference",
    clause="6.5.1",
    severity=Severity.ERROR,
    title="На рисунок нет ссылки в тексте",
)
def figure_no_reference(doc: Document) -> Iterable[Finding]:
    referenced = referenced_labels(doc)
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            yield figure_no_reference.finding(
                doc,
                environment.span,
                message="У рисунка нет метки, сослаться на него в тексте нечем.",
                requirement=REQUIREMENT,
                suggestion="Добавить \\label{fig:...} после \\caption и сослаться \\ref{fig:...}.",
            )
            continue
        if any(key in referenced for key in keys):
            continue
        yield figure_no_reference.finding(
            doc,
            environment.span,
            message=f"На рисунок с меткой {keys[0]!r} нет ссылки в тексте.",
            requirement=REQUIREMENT,
            suggestion=f"Добавить в текст ссылку: на рисунке~\\ref{{{keys[0]}}}.",
        )
