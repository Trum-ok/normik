"""Буквы, недопустимые в перечислениях."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import ITEM_COMMAND, parse_enumeration_label

#: Буквы, которые в перечислениях не используют: неотличимы от других букв
#: или от цифр в мелком кегле. Латинские I и O добавляет профиль стандарта,
#: который латиницу в обозначениях допускает.
FORBIDDEN_LETTERS = "ёзйочъыь"


@rule(
    id="enumeration-letters",
    standards={G732: "6.4.6", GR2105: "6.7.5"},
    severity=Severity.ERROR,
    title="В перечислении использована недопустимая буква",
    params={"forbidden": FORBIDDEN_LETTERS},
    deprecated_ids=("G732-6.4.6-enumeration-letters",),
)
def enumeration_letters(doc: Document) -> Iterable[Finding]:
    r"""Проверяет буквенные обозначения элементов перечисления, заданные явно —
    `\item[а)]` и подобные.

    ## Почему это нарушение

    Элементы перечисления обозначают строчными буквами русского алфавита начиная
    с «а», пропуская ё, з, й, о, ч, ъ, ы и ь: они неотличимы от других букв или
    от цифр в мелком кегле.

    ## Как исправить

    Заменить букву на следующую допустимую по порядку и сдвинуть обозначения
    остальных элементов перечисления.
    """
    forbidden = str(enumeration_letters.params(doc)["forbidden"]).casefold()
    listed = ", ".join(forbidden)
    for command in doc.structure.find_commands(ITEM_COMMAND):
        for option in command.options:
            parsed = parse_enumeration_label(option)
            if parsed is None:
                continue
            letter = parsed[0]
            if letter.casefold() not in forbidden:
                continue
            yield enumeration_letters.finding(
                doc,
                command.span,
                message=f"Элемент перечисления обозначен буквой «{letter}».",
                requirement=(
                    "Элементы перечисления обозначают строчными буквами по алфавиту, "
                    f"за исключением букв {listed}."
                ),
                suggestion="Заменить букву на следующую допустимую по порядку.",
                col=command.col,
            )
