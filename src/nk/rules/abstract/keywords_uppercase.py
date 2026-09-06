"""Регистр ключевых слов."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import KeywordList, keyword_lists

#: Обратная косая и доллар выдают команду или формулу: их регистр менять нельзя.
MARKUP = ("\\", "$")


@rule(
    id="G732-6.12.2-keywords-uppercase",
    standards={G732: "6.12.2"},
    severity=Severity.ERROR,
    title="Ключевые слова набраны не прописными буквами",
    fixable=True,
)
def keywords_uppercase(doc: Document) -> Iterable[Finding]:
    r"""Проверяет, что каждое ключевое слово набрано прописными буквами.

    ## Почему это нарушение

    Ключевые слова приводят в именительном падеже прописными буквами, в строку,
    через запятые — так они отделяются от остального текста реферата.

    ## Как исправить

    Записать перечень прописными буквами. Регистр задаётся текстом, а не командой
    оформления: `\MakeUppercase` в исходнике правило не увидит.
    """
    for entry in keyword_lists(doc):
        lowercase = [word for word in entry.words if word != word.upper()]
        if not lowercase:
            continue
        yield keywords_uppercase.finding(
            doc,
            entry.line,
            message=f"Ключевые слова набраны не прописными: {', '.join(lowercase[:3])}.",
            requirement=(
                "Ключевые слова приводят в именительном падеже прописными буквами, "
                "в строку, через запятые."
            ),
            suggestion=f"Записать прописными: {', '.join(word.upper() for word in entry.words)}.",
            fix=_uppercased(entry),
        )


def _uppercased(entry: KeywordList) -> Fix | None:
    """Правка поднимает регистр всего перечня — разметку в нём она бы испортила."""
    text = entry.inline
    if text is None or any(marker in text for marker in MARKUP):
        return None
    region = Region.in_line(entry.line.path, entry.line.lineno, entry.col, entry.col + len(text))
    return Fix(region, text.upper())
