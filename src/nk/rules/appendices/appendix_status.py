"""Статус приложения под его обозначением."""

import re
from collections.abc import Iterable

from nk.core.document import Document, Span
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import appendix_spans, visible_text

#: Статусы приложения: обязательное либо информационное — рекомендуемое или справочное.
STATUSES = ("обязательное", "рекомендуемое", "справочное")

#: Статус приводят в скобках отдельной строкой под обозначением.
STATUS_LINE = re.compile(r"^\(\s*(?P<status>[^)]+?)\s*\)$")

#: Сколько строк под заголовком просматривать: статус стоит сразу под ним.
LOOKAHEAD = 3


@rule(
    id="appendix-status",
    standards={GR2105: "6.3.4"},
    severity=Severity.ERROR,
    title="Под обозначением приложения не указан его статус",
    allow_missing_suggestion=True,
)
def appendix_status(doc: Document) -> Iterable[Finding]:
    """Просматривает первые непустые строки под заголовком приложения и ищет среди
    них статус в скобках. Заголовок самого приложения статусу не мешает: он может
    стоять и до, и после него.

    ## Почему это нарушение

    Статус говорит, обязательно приложение к исполнению или приведено для
    сведения. Без него читающий не знает, требование перед ним или пояснение.

    ## Как исправить

    Добавить под обозначением приложения отдельную строку со статусом
    в скобках: `(обязательное)`, `(рекомендуемое)` либо `(справочное)`.
    """
    for command, letter, span in appendix_spans(doc):
        found = _status(doc, span)
        if found in STATUSES:
            continue
        listed = ", ".join(STATUSES)
        message = (
            f"У приложения {letter} статус не указан."
            if found is None
            else f"У приложения {letter} указан статус «{found}», которого нет в стандарте."
        )
        yield appendix_status.finding(
            doc,
            command.span,
            message=message,
            requirement=f"Под обозначением приложения указывают его статус: {listed}.",
            col=command.col,
        )


def _status(doc: Document, span: Span) -> str | None:
    """Статус из ближайших строк под заголовком либо ``None``, если его там нет."""
    lines = doc.lines_of(span.path)[span.start : span.end]
    seen = 0
    for line in lines:
        text = visible_text(line.stripped).strip()
        if not text:
            continue
        match = STATUS_LINE.match(text)
        if match is not None:
            return match.group("status").casefold()
        seen += 1
        if seen >= LOOKAHEAD:
            return None
    return None
