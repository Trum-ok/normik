"""Порядок приложений относительно ссылок на них."""

from collections.abc import Iterable

from nk.core.document import Document, Span
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import APPENDIX_REFERENCE, appendix_spans, is_full_document


@rule(
    id="appendix-order",
    standards={G732: "6.17.2", GR2105: "6.3.3"},
    severity=Severity.ERROR,
    title="Приложения идут не в порядке ссылок на них",
    deprecated_ids=("G732-6.17.2-appendix-order",),
)
def appendix_order(doc: Document) -> Iterable[Finding]:
    """Сопоставляет порядок приложений с порядком первых упоминаний вида
    «в приложении А» в тексте. Упоминания внутри самих приложений не считаются:
    ссылка одного приложения на другое порядок не задаёт. Приложение, на которое
    ссылок нет, порядок не нарушает — его разбирает отдельное правило. Работает
    только на полном документе.

    ## Почему это нарушение

    Приложения располагают в порядке ссылок на них: читатель, дойдя до первой
    ссылки, находит нужное приложение первым, а не листает их все подряд.

    ## Как исправить

    Переставить приложения в порядке первых ссылок и переобозначить их буквами
    подряд либо изменить порядок изложения в основной части.
    """
    if not is_full_document(doc):
        return

    appendices = appendix_spans(doc)
    mentions = _first_mentions(doc, [span for _, _, span in appendices])

    previous_letter = ""
    previous_place = -1
    for command, letter, _ in appendices:
        place = mentions.get(letter)
        if place is None:
            continue
        if place >= previous_place:
            previous_letter, previous_place = letter, place
            continue
        yield appendix_order.finding(
            doc,
            command.span,
            message=(
                f"Приложение {letter} упомянуто в тексте раньше приложения "
                f"{previous_letter}, но стоит после него."
            ),
            requirement="Приложения располагают в порядке ссылок на них в тексте отчёта.",
            suggestion=f"Переставить приложение {letter} выше приложения {previous_letter}.",
            col=command.col,
        )
        previous_letter, previous_place = letter, place


def _first_mentions(doc: Document, spans: list[Span]) -> dict[str, int]:
    """Порядковый номер первого упоминания каждого приложения в основном тексте."""
    found: dict[str, int] = {}
    order = 0
    for line in doc.iter_lines():
        if any(span.path == line.path and span.contains(line.lineno) for span in spans):
            continue
        for match in APPENDIX_REFERENCE.finditer(line.stripped):
            found.setdefault(match.group(1), order)
            order += 1
    return found
