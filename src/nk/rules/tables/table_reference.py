"""Ссылка в тексте на каждую таблицу."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import TABLE_ENVIRONMENTS, float_no_reference

REQUIREMENT = "На все таблицы в отчёте должны быть ссылки со словом «таблица» и её номером."


@rule(
    id="G732-6.6.2-table-no-reference",
    standards={G732: "6.6.2"},
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
    return float_no_reference(
        table_no_reference,
        doc,
        TABLE_ENVIRONMENTS,
        requirement=REQUIREMENT,
        unlabelled="У таблицы нет метки, сослаться на неё в тексте нечем.",
        unlabelled_suggestion="Добавить \\label{tab:...} после \\caption и сослаться \\ref{tab:...}.",
        missing=lambda key: f"На таблицу с меткой {key!r} нет ссылки в тексте.",
        missing_suggestion=lambda key: f"Добавить в текст ссылку: в таблице~\\ref{{{key}}}.",
    )
