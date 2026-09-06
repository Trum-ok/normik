"""Алфавитный порядок в перечне сокращений."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import ABBREVIATIONS_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import listing_order


@rule(
    id="G732-6.15-abbreviations-order",
    clause="6.15",
    severity=Severity.ERROR,
    title="Сокращения в перечне идут не по алфавиту",
)
def abbreviations_order(doc: Document) -> Iterable[Finding]:
    """Сравнивает сокращения перечня между собой по алфавиту. Записью считается
    строка с расшифровкой справа от тире, поэтому вводная фраза перечня
    в сравнение не попадает. Регистр не различается, «ё» приравнивается к «е».
    Латинские сокращения сравниваются между собой, а не с русскими: перечень,
    в котором кириллица идёт перед латиницей, нарушением не считается.

    ## Почему это нарушение

    Перечень сокращений ведут по алфавиту: в него заглядывают за расшифровкой
    одного обозначения, а не читают целиком.

    ## Как исправить

    Переставить запись выше — на то место, которое ей отводит алфавит.
    """
    return listing_order(
        abbreviations_order,
        doc,
        doc.profile.elements.role(ABBREVIATIONS_ROLE),
        noun="Сокращение",
        requirement="Сокращения и обозначения в перечне располагают в алфавитном порядке.",
    )
