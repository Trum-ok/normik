"""Ссылка на нумерованную формулу."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    MATH_ENVIRONMENTS,
    is_numbered_environment,
    labels,
    referenced_labels,
)

REQUIREMENT = "Порядковый номер присваивают формулам, на которые в тексте есть ссылки."


@rule(
    id="G732-6.8.3-formula-no-reference",
    clause="6.8.3",
    severity=Severity.WARNING,
    title="Формула пронумерована, но ссылки на неё нет",
)
def formula_no_reference(doc: Document) -> Iterable[Finding]:
    referenced = referenced_labels(doc)
    for environment in doc.structure.find_environments(*MATH_ENVIRONMENTS):
        if not is_numbered_environment(environment.name):
            continue
        keys = [command.arg for command in labels(environment) if command.arg]
        if any(key in referenced for key in keys):
            continue
        starred = f"{environment.name}*"
        yield formula_no_reference.finding(
            doc,
            environment.span,
            message=f"Формула в окружении {environment.name} нумеруется, но ссылки на неё нет.",
            requirement=REQUIREMENT,
            suggestion=f"Сослаться на формулу через \\eqref либо снять нумерацию: {starred}.",
        )
