"""Нумерованная рубрика внутри приложения."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import appendix_spans, heading_text, ordered_headings


@rule(
    id="G732-6.17.6-appendix-numbering",
    clause="6.17.6",
    severity=Severity.ERROR,
    title="Рубрика внутри приложения нумеруется без его обозначения",
)
def appendix_internal_numbering(doc: Document) -> Iterable[Finding]:
    """Проверяет нумерацию разделов и подразделов внутри приложения.

    ## Почему это нарушение

    Текст приложения нумеруют в пределах самого приложения, а перед номером
    ставят его обозначение: А.1, А.1.1. Заголовок приложения оформляется через
    `\\section*` и счётчика не двигает, поэтому вложенная нумерованная рубрика
    получает номер из основной части отчёта.

    ## Как исправить

    Оформить рубрику через `\\subsection*` и вписать обозначение в заголовок,
    либо перевести приложения на `\\appendix` — тогда номера формирует класс.
    """
    headings = ordered_headings(doc)
    for command, letter, span in appendix_spans(doc):
        if not command.name.endswith("*"):
            continue
        for nested in headings:
            if nested.path != span.path or nested is command:
                continue
            if not span.contains(nested.lineno) or nested.name.endswith("*"):
                continue
            yield appendix_internal_numbering.finding(
                doc,
                nested.span,
                message=(
                    f"Рубрика «{heading_text(nested)}» внутри приложения {letter} "
                    "получает номер из основной части отчёта."
                ),
                requirement=(
                    "Разделы и подразделы приложения нумеруют в пределах самого "
                    "приложения, ставя перед номером его обозначение."
                ),
                suggestion=f"\\{nested.name}*{{{letter}.1 {heading_text(nested)}}}",
                col=nested.col,
            )
