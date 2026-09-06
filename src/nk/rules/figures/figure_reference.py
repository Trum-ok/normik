"""Ссылка в тексте на каждый рисунок."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import FIGURE_ENVIRONMENTS, float_no_reference

REQUIREMENT = "На все иллюстрации в отчёте должны быть даны ссылки со словом «рисунок» и номером."


@rule(
    id="figure-no-reference",
    standards={G732: "6.5.1", GR2105: "6.9.3"},
    severity=Severity.ERROR,
    title="На рисунок нет ссылки в тексте",
    deprecated_ids=("G732-6.5.1-figure-no-reference",),
)
def figure_no_reference(doc: Document) -> Iterable[Finding]:
    r"""Собирает метки рисунков и ссылки на них в тексте. Находка выдаётся на рисунок
    без ссылки, а также на рисунок без метки — сослаться на него нечем.

    ## Почему это нарушение

    На все иллюстрации в отчёте должны быть даны ссылки со словом «рисунок»
    и номером: иллюстрация поясняет текст, а не существует отдельно от него.
    По ссылкам определяется и порядок размещения иллюстраций.

    ## Как исправить

    Добавить `\label` после `\caption` и сослаться на рисунок в том абзаце,
    который он поясняет.
    """
    return float_no_reference(
        figure_no_reference,
        doc,
        FIGURE_ENVIRONMENTS,
        requirement=REQUIREMENT,
        unlabelled="У рисунка нет метки, сослаться на него в тексте нечем.",
        unlabelled_suggestion="Добавить \\label{fig:...} после \\caption и сослаться \\ref{fig:...}.",
        missing=lambda key: f"На рисунок с меткой {key!r} нет ссылки в тексте.",
        missing_suggestion=lambda key: f"Добавить в текст ссылку: на рисунке~\\ref{{{key}}}.",
    )
