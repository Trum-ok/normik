"""Внутренние диагностики линтера.

Это не правила: они не проверяют требований стандарта, не имеют пункта и фикстур.
Но отключать их профилем и ключом ``--ignore`` нужно так же, как правила, поэтому
их идентификаторы перечислены здесь.
"""

from dataclasses import dataclass
from pathlib import Path

from nk.core.finding import Finding, Severity

#: Диагностики не ссылаются на пункт стандарта.
NO_CLAUSE = ""

INPUT_MISSING = "NK-PARSE-001"
INPUT_CYCLE = "NK-PARSE-002"
ENVIRONMENT_UNCLOSED = "NK-PARSE-003"
ENVIRONMENT_ORPHAN_END = "NK-PARSE-004"
GROUP_UNCLOSED = "NK-PARSE-005"
ENCODING_FALLBACK = "NK-PARSE-006"
IGNORE_UNUSED = "NK-IGNORE-001"
IGNORE_UNKNOWN = "NK-IGNORE-002"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: Severity
    title: str


INTERNAL: dict[str, Diagnostic] = {
    item.code: item
    for item in (
        Diagnostic(INPUT_MISSING, Severity.INFO, "Включаемый файл не найден"),
        Diagnostic(INPUT_CYCLE, Severity.INFO, "Циклическое включение файла"),
        Diagnostic(ENVIRONMENT_UNCLOSED, Severity.INFO, "Окружение не закрыто"),
        Diagnostic(ENVIRONMENT_ORPHAN_END, Severity.INFO, "\\end без парного \\begin"),
        Diagnostic(GROUP_UNCLOSED, Severity.INFO, "Не закрыта скобка аргумента"),
        Diagnostic(ENCODING_FALLBACK, Severity.INFO, "Файл не в UTF-8"),
        Diagnostic(IGNORE_UNUSED, Severity.WARNING, "Подавление ничего не подавило"),
        Diagnostic(IGNORE_UNKNOWN, Severity.WARNING, "Подавление ссылается на неизвестное правило"),
    )
}


def to_finding(
    code: str,
    *,
    message: str,
    requirement: str,
    path: Path,
    lineno: int,
    col: int | None = None,
    suggestion: str | None = None,
    excerpt: str | None = None,
    context: tuple[str, ...] = (),
) -> Finding:
    """Находка по внутренней диагностике: уровень берётся из её объявления.

    Диагностики рождаются в двух местах — у парсера и у проверки директив
    подавления, — а уровень у них один и тот же и объявлен здесь.
    """
    return Finding(
        rule_id=code,
        clause=NO_CLAUSE,
        severity=INTERNAL[code].severity,
        message=message,
        requirement=requirement,
        path=path,
        lineno=lineno,
        col=col,
        excerpt=excerpt,
        context=context,
        suggestion=suggestion,
    )
