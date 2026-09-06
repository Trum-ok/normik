"""Вводная формулировка перед списком перечислений."""

from collections.abc import Iterable

from nk.core.document import Document, Environment
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import LIST_ENVIRONMENTS, visible_text

COLON = ":"


@rule(
    id="enumeration-opening-colon",
    standards={GR2105: "6.7.1"},
    severity=Severity.ERROR,
    title="Перед списком перечислений нет вводной формулировки с двоеточием",
    allow_missing_suggestion=True,
)
def enumeration_opening_colon(doc: Document) -> Iterable[Finding]:
    r"""Смотрит ближайшую непустую строку выше `\begin` списка и проверяет двоеточие
    в её конце. Строка с `\item` подходит: вложенный список вводит текст своего
    элемента.

    ## Почему это нарушение

    Список перечислений относится к формулировке, которая его вводит: без неё
    читающий не знает, что именно перечисляется. Двоеточие в конце этой
    формулировки и связывает её со списком.

    ## Как исправить

    Дописать перед списком фразу, которая относится ко всему списку, и
    закончить её двоеточием.
    """
    for environment in doc.structure.find_environments(*LIST_ENVIRONMENTS):
        opening = _opening(doc, environment)
        if opening is None or opening.endswith(COLON):
            continue
        shown = f"«{opening[-40:]}»" if opening else "пустая строка"
        yield enumeration_opening_colon.finding(
            doc,
            environment.span,
            message=f"Перед списком стоит {shown}, а не формулировка с двоеточием.",
            requirement=(
                "Перед списком перечислений приводят формулировку, относящуюся ко "
                "всему списку, и заканчивают её двоеточием."
            ),
        )


def _opening(doc: Document, environment: Environment) -> str | None:
    """Видимый текст ближайшей непустой строки выше списка.

    ``None`` — выше ничего нет: список открывает файл, и вводная формулировка
    могла остаться в файле, который его включает.
    """
    lines = doc.lines_of(environment.path)
    for line in reversed(lines[: environment.span.start - 1]):
        text = visible_text(line.stripped).strip()
        if text:
            return text
    return None
