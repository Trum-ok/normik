"""Перенос слова в заголовке рубрики."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import HYPHENATION_MARKER, heading_text, headings, without_hyphenation


@rule(
    id="G732-6.2.4-heading-hyphenation",
    clause="6.2.4",
    severity=Severity.ERROR,
    title="В заголовке задан перенос слова",
    fixable=True,
)
def heading_hyphenation(doc: Document) -> Iterable[Finding]:
    r"""Ищет в заголовке заданную вручную точку переноса `\-`.

    ## Почему это нарушение

    Переносы слов в заголовках не допускаются. Заданная точка переноса рано или
    поздно срабатывает: при смене кегля, полей или редакции текста.

    ## Как исправить

    Убрать `\-` из заголовка. Если строка не умещается, сократить заголовок либо
    разбить его командой разрыва строки по границе слова.
    """
    for command in headings(doc):
        if HYPHENATION_MARKER not in heading_text(command):
            continue
        yield heading_hyphenation.finding(
            doc,
            command.span,
            message="В заголовке задана точка переноса «\\-».",
            requirement="Переносы слов в заголовках не допускаются.",
            suggestion="Убрать «\\-» из заголовка.",
            col=command.col,
            fix=without_hyphenation(doc, command),
        )
