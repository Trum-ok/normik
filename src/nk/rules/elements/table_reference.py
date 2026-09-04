"""Ссылка в тексте на каждую таблицу."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import TABLE_ENVIRONMENTS, labels, referenced_labels

REQUIREMENT = "На все таблицы в отчёте должны быть ссылки со словом «таблица» и её номером."


@rule(
    id="G732-6.6.2-table-no-reference",
    clause="6.6.2",
    severity=Severity.ERROR,
    title="На таблицу нет ссылки в тексте",
)
def table_no_reference(doc: Document) -> Iterable[Finding]:
    r"""Собирает метки таблиц и ссылки на них в тексте. Находка выдаётся на таблицу
    без ссылки, а также на таблицу без метки.

    ## Почему это нарушение

    На все таблицы в отчёте должны быть ссылки со словом «таблица» и её номером.
    Таблица, на которую нет ссылки, не связана с изложением.

    ## Как исправить

    Добавить `\label` после `\caption` и сослаться на таблицу в тексте.
    """
    referenced = referenced_labels(doc)
    for environment in doc.structure.find_environments(*TABLE_ENVIRONMENTS):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            yield table_no_reference.finding(
                doc,
                environment.span,
                message="У таблицы нет метки, сослаться на неё в тексте нечем.",
                requirement=REQUIREMENT,
                suggestion="Добавить \\label{tab:...} после \\caption и сослаться \\ref{tab:...}.",
            )
            continue
        if any(key in referenced for key in keys):
            continue
        yield table_no_reference.finding(
            doc,
            environment.span,
            message=f"На таблицу с меткой {keys[0]!r} нет ссылки в тексте.",
            requirement=REQUIREMENT,
            suggestion=f"Добавить в текст ссылку: в таблице~\\ref{{{keys[0]}}}.",
        )
