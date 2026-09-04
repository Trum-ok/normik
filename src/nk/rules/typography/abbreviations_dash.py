"""Дефис вместо тире в перечне: сокращение."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import ABBREVIATION_ELEMENTS
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import listing_dash


@rule(
    id="G732-6.15-abbreviations-dash",
    clause="6.15",
    severity=Severity.WARNING,
    title="В перечне сокращений расшифровка отделена дефисом",
    fixable=True,
)
def abbreviations_dash(doc: Document) -> Iterable[Finding]:
    """Проверяет знак, отделяющий сокращение от расшифровки.

    ## Почему это нарушение

    Стандарт требует отделять правую часть тире. Дефис — другой знак, и в
    наборе он заметно короче.

    ## Как исправить

    Заменить дефис на тире.
    """
    return listing_dash(
        abbreviations_dash,
        doc,
        ABBREVIATION_ELEMENTS,
        "В перечне сокращений расшифровку приводят справа через тире.",
    )
