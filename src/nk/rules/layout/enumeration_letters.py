"""Буквы, недопустимые в перечислениях."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule

#: Буквы, которые в перечислениях не используют.
FORBIDDEN_LETTERS = frozenset("ёзйочъыь")

_LABEL = re.compile(r"^\s*([а-яё])\s*\)?\s*$")


@rule(
    id="G732-6.4.6-enumeration-letters",
    clause="6.4.6",
    severity=Severity.ERROR,
    title="В перечислении использована недопустимая буква",
)
def enumeration_letters(doc: Document) -> Iterable[Finding]:
    for command in doc.structure.find_commands("item"):
        for option in command.options:
            match = _LABEL.match(option)
            if match is None:
                continue
            letter = match.group(1)
            if letter not in FORBIDDEN_LETTERS:
                continue
            yield enumeration_letters.finding(
                doc,
                command.span,
                message=f"Элемент перечисления обозначен буквой «{letter}».",
                requirement=(
                    "Элементы перечисления обозначают строчными буквами русского алфавита "
                    "начиная с «а», за исключением ё, з, й, о, ч, ъ, ы, ь."
                ),
                suggestion="Заменить букву на следующую допустимую по порядку.",
                col=command.col,
            )
