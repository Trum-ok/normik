"""Обозначение стандарта без регистрационного номера."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._text import is_code, prose

#: Индексы документов по стандартизации. За индексом идёт регистрационный номер.
INDEXES = ("ГОСТ", "ОСТ", "СТО", "СНиП", "ТУ")

#: Индекс, за которым нет числа: «ГОСТ» и «ГОСТ Р» без номера. Буква «Р»
#: национального стандарта числом не считается и номер не заменяет.
_WITHOUT_NUMBER = re.compile(
    r"\b(?P<index>" + "|".join(INDEXES) + r")(?![\wА-Яа-яЁё])(?:\s+Р)?(?!\s*[\dР])"
)


@rule(
    id="standard-without-number",
    standards={GR2105: "5.2.4"},
    severity=Severity.WARNING,
    title="Обозначение стандарта приведено без регистрационного номера",
    allow_missing_suggestion=True,
)
def standard_without_number(doc: Document) -> Iterable[Finding]:
    """Ищет индексы документов по стандартизации, за которыми не идёт число.
    Формулы, таблицы и буквальные вставки не проверяются.

    ## Почему это нарушение

    Один индекс не определяет документ: стандартов с индексом «ГОСТ» тысячи,
    и по такой ссылке требование не найти.

    ## Как исправить

    Дописать регистрационный номер: «ГОСТ 7.32-2017». Год утверждения
    допускается не указывать, если он приведён в перечне ссылочных документов.
    """
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        for match in _WITHOUT_NUMBER.finditer(prose(doc, line)):
            index = match.group("index")
            yield standard_without_number.finding(
                doc,
                line,
                message=f"Индекс «{index}» приведён без регистрационного номера.",
                requirement=(
                    "Индексы стандартов, технических условий и других документов "
                    "приводят с регистрационным номером."
                ),
                col=match.start() + 1,
            )
