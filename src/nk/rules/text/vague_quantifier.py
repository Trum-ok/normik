"""Мера изменения или количества, приведённая без числа."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import Origin
from nk.rules._wording import HARD, forms, has_measure, mentions, pattern, terms

#: Прилагательные неопределённой меры: основа и окончания, которые она принимает.
ADJECTIVES: dict[str, str] = {
    "значительн": HARD,
    "незначительн": HARD,
    "существенн": HARD,
    "несущественн": HARD,
    "заметн": HARD,
}

#: Наречия меры и усилители.
ADVERBS = (
    "значительно существенно намного гораздо заметно резко сильно "
    "очень весьма крайне чрезвычайно довольно достаточно "
    "много немного мало немало"
)

#: Устойчивые сочетания, в которых слово меры не обозначает: «достаточное
#: условие» — термин, «достаточно для» — сообщение о том, что чего-то хватает.
TERMS = (
    r"достаточн\w* услови\w*",
    r"необходим\w* и достаточн\w*",
    r"достаточно,?\s+(?:для|чтобы|ли)",
    # «достаточно рассмотреть один случай» — сообщение о том, что этого хватает.
    r"достаточно,?\s+\w+(?:ть|ться)\b",
    r"существенно нелинейн\w*",
)

_WORDS = pattern(forms(ADJECTIVES), ADVERBS)
_TERMS = terms(*TERMS)


@rule(
    id="vague-quantifier",
    origin=Origin.REGULATION,
    severity=Severity.WARNING,
    title="Мера приведена без числа",
    params={"headings": False, "allow": [], "require_number": True},
)
def vague_quantifier(doc: Document) -> Iterable[Finding]:
    """Ищет меру без числа: «значительно вырос», «существенно меньше», «довольно
    много». Формулы, листинги, список источников и рубрикация не проверяются.

    Замечание снимается, когда величина названа в том же предложении: число,
    диапазон, доля или ссылка на таблицу, рисунок либо формулу, где значение
    приведено. «Быстродействие выросло значительно, с 120 до 40 мс» — мера
    подкреплена, замечания нет. Проверку числом выключает параметр
    `require_number`: тогда мера считается замечанием всегда.

    Слово, которое на кафедре считают термином, добавляется параметром `allow`
    началом слова. Проверку заголовков включает параметр `headings`.

    ## Почему это замечание

    «Значительно» само по себе шкалы не имеет: во сколько раз и с чего до чего —
    из текста не следует, а вывод о результате читатель делает по числу.

    ## Как исправить

    Привести значение рядом со словом или вместо него: «значительно выросло» →
    «выросло на 35 %», «существенно меньше» → «меньше в 4 раза».
    """
    params = vague_quantifier.params(doc)
    require_number = bool(params["require_number"])
    found = mentions(
        doc,
        _WORDS,
        exceptions=_TERMS,
        allow=params["allow"],
        headings=bool(params["headings"]),
    )
    for mention in found:
        if require_number and has_measure(mention.sentence):
            continue
        yield vague_quantifier.finding(
            doc,
            mention.line,
            message=f"Мера «{mention.found}» приведена без числа.",
            requirement=(
                "Меру изменения или количества приводят числом: значением, диапазоном "
                "или долей, а не наречием."
            ),
            suggestion=(
                f"Указать рядом с «{mention.found}» значение: «на 35 %», «с 120 до 40 мс»."
            ),
            col=mention.col,
        )
