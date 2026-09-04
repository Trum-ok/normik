"""Алфавитный порядок в перечне терминов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import alphabet_key, alphabet_of, listing_entries

ELEMENTS = frozenset({"ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"})


@rule(
    id="G732-6.14-terms-order",
    clause="6.14",
    severity=Severity.ERROR,
    title="Термины в перечне идут не по алфавиту",
)
def terms_order(doc: Document) -> Iterable[Finding]:
    """Сравнивает термины перечня между собой по алфавиту. Записью считается строка
    с определением справа от тире, поэтому вводная фраза перечня в сравнение
    не попадает. Регистр не различается, «ё» приравнивается к «е». Термины
    на латинице сравниваются между собой, а не с русскими: переход к латинскому
    алфавиту нарушением не считается.

    ## Почему это нарушение

    Перечень терминов ведут по алфавиту: он нужен для справок, а искать в нём
    подряд, как в связном тексте, никто не будет.

    ## Как исправить

    Переставить запись выше — на то место, которое ей отводит алфавит.
    """
    previous_term = ""
    previous_key = ""
    previous_alphabet = ""
    for line, term in listing_entries(doc, ELEMENTS):
        key, alphabet = alphabet_key(term), alphabet_of(term)
        if alphabet != previous_alphabet or key >= previous_key:
            previous_term, previous_key, previous_alphabet = term, key, alphabet
            continue
        yield terms_order.finding(
            doc,
            line,
            message=f"Термин «{term}» стоит после «{previous_term}», хотя по алфавиту идёт раньше.",
            requirement="Термины в перечне располагают в алфавитном порядке.",
            suggestion=f"Переставить запись «{term}» выше записи «{previous_term}».",
        )
        previous_term, previous_key, previous_alphabet = term, key, alphabet
