"""Знак вместо слова перед числовым значением."""

import re
from collections.abc import Iterable, Iterator

from nk.core.document import Document, Line
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._text import is_code, prose

#: Знак перед числовым значением и слово, которым его записывают.
SIGNS: dict[str, str] = {"-": "минус", "−": "минус", "+": "плюс"}

#: Обозначения диаметра: слово вместо знака нужно везде, не только перед числом.
DIAMETER = "⌀Ø∅"

#: Знак стоит перед числом и не примыкает к слову или другому числу: «-5»,
#: но не «изделие-2» и не «от 5-10».
_BEFORE_NUMBER = re.compile(r"(?<![\w\d\-−+])([-−+])\d")
_DIAMETER = re.compile(f"[{DIAMETER}]")


@rule(
    id="sign-instead-of-word",
    standards={GR2105: "5.2.4"},
    severity=Severity.WARNING,
    title="Знак приведён вместо слова",
)
def sign_instead_of_word(doc: Document) -> Iterable[Finding]:
    """Ищет минус, плюс и знак диаметра в тексте. Формулы, таблицы и буквальные
    вставки не проверяются: там знак — часть записи. Дефис между словами и тире
    между числами правило не трогает: знаком величины они не являются.

    ## Почему это нарушение

    В тексте документа математический знак перед значением величины заменяют
    словом: «минус 40» не спутать с переносом или с тире, а «-40» — можно.

    ## Как исправить

    Написать слово: «минус 40», «плюс 10», «диаметр 20».
    """
    for line, found, word, col in _signs(doc):
        yield sign_instead_of_word.finding(
            doc,
            line,
            message=f"Вместо слова «{word}» приведён знак «{found}».",
            requirement=(
                "В тексте перед значением величины пишут слово «минус», «плюс» "
                "или «диаметр», а не знак."
            ),
            suggestion=f"Заменить «{found}» на слово «{word}».",
            col=col,
        )


def _signs(doc: Document) -> Iterator[tuple[Line, str, str, int]]:
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        text = prose(doc, line)
        for match in _BEFORE_NUMBER.finditer(text):
            sign = match.group(1)
            yield line, sign, SIGNS[sign], match.start(1) + 1
        for match in _DIAMETER.finditer(text):
            yield line, match.group(0), "диаметр", match.start() + 1
