"""Местоимение первого лица в тексте отчёта."""

import re
from collections.abc import Iterable, Iterator

from nk.core.document import Document, Line
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import Origin
from nk.rules._text import at_sentence_start, is_code, prose

#: Личные и притяжательные местоимения первого лица единственного числа.
SINGULAR = (
    "я меня мне мной мною мой моего моему моим моём моем моя моей мою моею моё мое мои моих моими"
)

#: Авторское «мы»: часть руководителей его допускает, а часть требует, поэтому
#: ловится оно только по параметру.
PLURAL = "мы нас нам нами наш нашего нашему нашим нашем наша нашей нашу наше наши наших нашими"


def _pattern(words: str) -> re.Pattern[str]:
    return re.compile(r"\b(?:" + "|".join(sorted(set(words.split()))) + r")\b", re.IGNORECASE)


_SINGULAR = _pattern(SINGULAR)
_ANY = _pattern(f"{SINGULAR} {PLURAL}")


@rule(
    id="first-person-pronoun",
    origin=Origin.REGULATION,
    severity=Severity.WARNING,
    title="Текст изложен от первого лица: местоимение",
    params={"plural": False},
    allow_missing_suggestion=True,
)
def first_person_pronoun(doc: Document) -> Iterable[Finding]:
    """Ищет местоимения первого лица во всех падежах, вместе с притяжательными.
    Формулы, буквальные вставки и листинги не проверяются.

    Авторское «мы» правило по умолчанию не трогает: часть руководителей его
    требует. Включается параметром `plural`.

    Безличного изложения ни один стандарт не требует: это требование положений
    вузов и методических указаний. Предъявляют его почти везде, поэтому правило
    включено по умолчанию.

    ## Почему это замечание

    Отчёт излагают безлично: сообщается, что сделано, а не кем. «Я настроил
    стенд» и «стенд настроен» несут одно и то же, но первое переводит текст
    из отчёта в рассказ о себе.

    ## Как исправить

    Переписать предложение безличной или страдательной конструкцией: «мною
    выполнен расчёт» → «выполнен расчёт», «в моей программе» → «в программе».
    """
    pattern = _ANY if first_person_pronoun.params(doc)["plural"] else _SINGULAR
    for line, found, col in _pronouns(doc, pattern):
        yield first_person_pronoun.finding(
            doc,
            line,
            message=f"Текст изложен от первого лица: «{found}».",
            requirement="Отчёт излагают безлично, без местоимений первого лица.",
            col=col,
        )


def _pronouns(doc: Document, pattern: re.Pattern[str]) -> Iterator[tuple[Line, str, int]]:
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        text = prose(doc, line)
        for match in pattern.finditer(text):
            found = match.group()
            # «я)» — обозначение элемента перечисления, а не местоимение.
            if found.casefold() == "я" and text[match.end() : match.end() + 1] == ")":
                continue
            # Заглавная посреди предложения — обозначение: приложение Я, раздел Наш.
            if found[0].isupper() and not at_sentence_start(text, match.start()):
                continue
            yield line, found, match.start() + 1
