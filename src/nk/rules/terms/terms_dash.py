"""Дефис вместо тире в перечне: термин."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.elements import TERMS_ROLE
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import listing_dash


@rule(
    id="terms-dash",
    standards={G732: "6.14"},
    severity=Severity.WARNING,
    title="В перечне терминов определение отделено дефисом",
    fixable=True,
    deprecated_ids=("G732-6.14-terms-dash",),
)
def terms_dash(doc: Document) -> Iterable[Finding]:
    """Проверяет знак, отделяющий термин от расшифровки.

    ## Почему это нарушение

    Стандарт требует отделять правую часть тире. Дефис — другой знак, и в
    наборе он заметно короче.

    ## Как исправить

    Заменить дефис на тире.
    """
    return listing_dash(
        terms_dash,
        doc,
        doc.profile.elements.role(TERMS_ROLE),
        "В перечне терминов определения приводят справа через тире.",
    )
