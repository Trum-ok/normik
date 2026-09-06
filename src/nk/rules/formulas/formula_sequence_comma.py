"""Знак между формулами, идущими подряд."""

from collections.abc import Iterable
from itertools import pairwise

from nk.core.document import Document, Environment
from nk.core.finding import Finding, Severity
from nk.core.math import MATH_ENVIRONMENTS
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import visible_text

SEPARATORS = (",", ";", ".")


@rule(
    id="formula-sequence-comma",
    standards={GR2105: "6.10.1"},
    severity=Severity.WARNING,
    title="Формулы идут подряд без разделяющего знака",
    allow_missing_suggestion=True,
)
def formula_sequence_comma(doc: Document) -> Iterable[Finding]:
    """Ищет соседние выключные формулы, между которыми в исходнике нет текста,
    и проверяет знак в конце первой из них. Формулы, разделённые пояснением или
    любым другим текстом, правило не трогает.

    ## Почему это нарушение

    Формулы, следующие одна за другой и не разделённые текстом, разделяют
    запятой: иначе они читаются как одна разорванная формула.

    ## Как исправить

    Поставить запятую в конце первой формулы, перед закрывающей командой
    окружения.
    """
    for first, second in pairwise(_display_formulas(doc)):
        if first.path != second.path or _text_between(doc, first, second):
            continue
        tail = _tail(doc, first)
        if tail.endswith(SEPARATORS):
            continue
        yield formula_sequence_comma.finding(
            doc,
            first.span,
            message="За формулой сразу идёт следующая, а разделяющего знака нет.",
            requirement=(
                "Формулы, следующие одна за другой и не разделённые текстом, разделяют запятой."
            ),
        )


def _display_formulas(doc: Document) -> list[Environment]:
    """Выключные формулы в порядке следования по отчёту."""
    found = [
        environment
        for environment in doc.structure.walk_environments()
        if environment.name in MATH_ENVIRONMENTS
    ]
    return sorted(found, key=lambda item: (doc.file_index(item.path), item.span.start))


def _text_between(doc: Document, first: Environment, second: Environment) -> str:
    lines = doc.lines_of(first.path)[first.span.end : second.span.start - 1]
    return "".join(visible_text(line.stripped) for line in lines).strip()


def _tail(doc: Document, formula: Environment) -> str:
    """Последний непустой кусок формулы: там и стоит разделяющий знак."""
    lines = doc.lines_of(formula.path)[formula.span.start : formula.span.end - 1]
    for line in reversed(lines):
        text = line.stripped.strip()
        if text:
            return text
    return ""
