"""Математический знак без числового значения."""

import re
from collections.abc import Iterable, Iterator

from nk.core.document import Document, Line
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._text import is_code, prose

#: Знаки величин и их названия словами. Процент в LaTeX экранируют, иначе он
#: начинает комментарий и до правила не доходит.
SIGNS: dict[str, str] = {
    ">": "больше",
    "<": "меньше",
    "≥": "больше или равно",
    "≤": "меньше или равно",
    "≠": "не равно",
    "№": "номер",
    "\\%": "процент",
}

#: Сколько знаков вокруг просматривать в поисках числа.
NEIGHBOURHOOD = 4

_SIGNS = re.compile("|".join(re.escape(sign) for sign in sorted(SIGNS, key=len, reverse=True)))


@rule(
    id="math-sign-without-value",
    standards={GR2105: "5.2.4"},
    severity=Severity.WARNING,
    title="Математический знак приведён без числового значения",
)
def math_sign_without_value(doc: Document) -> Iterable[Finding]:
    r"""Ищет знаки величин в тексте и смотрит, есть ли рядом число. Формулы,
    таблицы и буквальные вставки не проверяются: там знак — часть записи,
    а не замена слову. Знак «равно» правило не ищет: в тексте он почти всегда
    часть формулы, а та уже вырезана.

    ## Почему это нарушение

    В тексте документа математические знаки величин без числовых значений не
    применяют: «> допустимого» читается как обрывок формулы, а «больше
    допустимого» — как фраза.

    ## Как исправить

    Заменить знак словом либо дописать числовое значение, к которому он
    относится.
    """
    for line, sign, col in _signs(doc):
        yield math_sign_without_value.finding(
            doc,
            line,
            message=f"Знак «{sign.lstrip(chr(92))}» приведён без числового значения.",
            requirement=(
                "В тексте математические знаки величин без числовых значений "
                "не применяют: их заменяют словами."
            ),
            suggestion=f"Заменить знак словом «{SIGNS[sign]}» либо дописать значение.",
            col=col,
        )


def _signs(doc: Document) -> Iterator[tuple[Line, str, int]]:
    """Знаки, рядом с которыми числа нет."""
    for line in doc.iter_lines():
        if is_code(doc, line):
            continue
        text = prose(doc, line)
        for match in _SIGNS.finditer(text):
            start, end = match.span()
            near = text[max(0, start - NEIGHBOURHOOD) : end + NEIGHBOURHOOD]
            if any(char.isdigit() for char in near):
                continue
            yield line, match.group(0), start + 1
