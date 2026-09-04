"""Прямые кавычки вместо «ёлочек»."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._text import is_code, prose

STRAIGHT = '"'
OPENING = "«"
CLOSING = "»"
PAIR = 2

#: Символы, превращающие кавычку в сокращение babel: «"=» — неразрывный дефис,
#: «"|» — запрет лигатуры, «"<» и «">» — сами ёлочки. Это команды набора,
#: а не кавычки, и трогать их нельзя.
SHORTHANDS = frozenset("=|-~<>,'`\"")


@rule(
    id="NK-STYLE-quotes",
    clause="",
    severity=Severity.INFO,
    title="Прямые кавычки вместо «ёлочек»",
    fixable=True,
)
def text_quotes(doc: Document) -> Iterable[Finding]:
    """Находит прямую кавычку `"` в тексте отчёта.

    ## Почему это замечание

    В русском наборе основные кавычки — «ёлочки». Прямая кавычка приходит из
    редактора кода и в отчёте выглядит инородно.

    ## Как исправить

    Заменить пару прямых кавычек на «ёлочки». Если кавычек на строке ровно две,
    правка делается автоматически; в остальных случаях границы пары
    определяются неоднозначно.

    Сокращения babel — `"=`, `"|`, `"<`, `">` и подобные — правило не трогает:
    это команды набора, а не кавычки.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        text = prose(doc, line)
        positions = _quotes(text)
        if not positions:
            continue

        pair = positions if len(positions) == PAIR else []
        for order, index in enumerate(positions):
            replacement = (OPENING if order == 0 else CLOSING) if pair else None
            yield text_quotes.finding(
                doc,
                line,
                message="В тексте использована прямая кавычка.",
                requirement="Основные кавычки русского набора — «ёлочки».",
                suggestion=f"Заменить прямые кавычки на {OPENING}{CLOSING}",
                col=index + 1,
                fix=(
                    Fix(
                        Region.in_line(line.path, line.lineno, index + 1, index + 2),
                        replacement,
                    )
                    if replacement is not None
                    else None
                ),
            )


def _quotes(text: str) -> list[int]:
    """Позиции прямых кавычек без сокращений babel."""
    found: list[int] = []
    index = 0
    while index < len(text):
        if text[index] != STRAIGHT:
            index += 1
            continue
        if text[index + 1 : index + 2] and text[index + 1] in SHORTHANDS:
            # Сокращение занимает два символа: вторая кавычка «""» тоже не кавычка.
            index += 2
            continue
        found.append(index)
        index += 1
    return found
