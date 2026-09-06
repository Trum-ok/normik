"""Регистр первой буквы элемента перечисления."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import LIST_ENVIRONMENTS, item_text, list_items


@rule(
    id="enumeration-lowercase",
    standards={GR2105: "6.7.1"},
    severity=Severity.WARNING,
    title="Элемент перечисления начат с прописной буквы",
    default_off=True,
    allow_missing_suggestion=True,
)
def enumeration_lowercase(doc: Document) -> Iterable[Finding]:
    r"""Смотрит первую букву текста элемента на той строке, где он начат.

    Стандарт разрешает прописную букву там, где она обязательна для первого
    слова, а имя собственное от обычного слова по исходникам не отличить.
    Аббревиатуру правило пропускает — слово целиком прописными не проверяется, —
    но «Москва» в начале элемента даст ложное срабатывание. Поэтому правило
    выключено по умолчанию.

    ## Почему это нарушение

    Элементы перечисления продолжают вводную формулировку, а не начинают новое
    предложение: прописная буква разрывает эту связь.

    ## Как исправить

    Заменить первую букву на строчную либо, если слово требует прописной,
    оставить как есть и отключить правило.
    """
    for environment in doc.structure.find_environments(*LIST_ENVIRONMENTS):
        for command in list_items(environment):
            word = item_text(doc, command).split(" ", 1)[0]
            letters = [char for char in word if char.isalpha()]
            if not letters or letters[0].islower() or all(char.isupper() for char in letters):
                continue
            yield enumeration_lowercase.finding(
                doc,
                command.span,
                message=f"Элемент перечисления начат с прописной буквы: «{word}».",
                requirement=(
                    "Текст перечисления начинают со строчной буквы, если прописная "
                    "не обязательна для первого слова."
                ),
                col=command.col,
            )
