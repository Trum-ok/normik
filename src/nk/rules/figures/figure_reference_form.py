"""Оборот ссылки на графический материал."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS

#: Упоминание рисунка с номером или ссылкой: «рисунком 2», «рисунке~\ref{...}».
MENTION = re.compile(
    r"\bрисун(?:ок|ка|ку|ком|ке|ки|ков|кам|ками|ках)\b\s*~?\s*(?:\d|\\(?:ref|autoref|cref))",
    re.IGNORECASE,
)

#: Оборот, который должен стоять перед упоминанием.
FORM = "в соответствии с"
_FORM = re.compile(r"в\s+соответствии\s+с\w*\s*$", re.IGNORECASE)


@rule(
    id="figure-reference-form",
    severity=Severity.WARNING,
    title="Ссылка на графический материал дана не установленным оборотом",
    default_off=True,
    allow_missing_suggestion=True,
)
def figure_reference_form(doc: Document) -> Iterable[Finding]:
    r"""Ищет упоминание рисунка с номером или `\ref` и смотрит, стоит ли перед ним
    оборот «в соответствии с». Подписи внутри окружений рисунка не проверяются:
    там номер часть наименования, а не ссылка.

    Ни один из стандартов оборота не предписывает, поэтому правило выключено
    по умолчанию. Включают его профилем того вуза, чьё положение этого требует.

    ## Почему это нарушение

    Положение вуза может задавать единственную форму ссылки на графический
    материал. Разнобой оборотов в одной работе читается как небрежность,
    а нормоконтроль его возвращает.

    ## Как исправить

    Переписать ссылку установленным оборотом: «в соответствии с рисунком 2».
    """
    covered = doc.structure.covered_lines(*FIGURE_ENVIRONMENTS)
    for line in doc.iter_lines():
        if (line.path, line.lineno) in covered:
            continue
        match = MENTION.search(line.stripped)
        if match is None or _FORM.search(line.stripped[: match.start()]):
            continue
        yield figure_reference_form.finding(
            doc,
            line,
            message=f"Ссылка на рисунок дана без оборота «{FORM}».",
            requirement=f"Ссылку на графический материал дают оборотом «{FORM} рисунком N».",
            col=match.start() + 1,
        )
