"""Знак препинания в конце записи перечня: термин."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import TERMS_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import listing_final_punctuation


@rule(
    id="terms-final-punctuation",
    standards={G732: "6.14", GR2105: "6.1.2"},
    severity=Severity.WARNING,
    title="Запись перечня терминов заканчивается знаком препинания",
    fixable=True,
)
def terms_final_punctuation(doc: Document) -> Iterable[Finding]:
    """Проверяет последний знак записи перечня терминов. Вводная фраза перечня
    записью не считается: разделителя в ней нет.

    ## Почему это нарушение

    Список терминологических статей располагают столбцом без знаков препинания
    в конце: запись — не предложение, и точка или точка с запятой в её конце
    сбивают ритм столбца.

    ## Как исправить

    Убрать знак препинания в конце записи.
    """
    return listing_final_punctuation(
        terms_final_punctuation,
        doc,
        doc.profile.elements.role(TERMS_ROLE),
        "Перечень терминов располагают столбцом без знаков препинания в конце строки.",
    )
