"""Замечания парсера.

Битый или непонятый TeX не роняет запуск: парсер сообщает о таких участках
находками уровня ``info`` и продолжает работу.
"""

from dataclasses import dataclass
from pathlib import Path

from nk.core.finding import Finding, Severity

#: Замечания парсера не ссылаются на пункт стандарта.
NO_CLAUSE = ""

INPUT_MISSING = "NK-PARSE-001"
INPUT_CYCLE = "NK-PARSE-002"
ENVIRONMENT_UNCLOSED = "NK-PARSE-003"
ENVIRONMENT_ORPHAN_END = "NK-PARSE-004"
GROUP_UNCLOSED = "NK-PARSE-005"
ENCODING_FALLBACK = "NK-PARSE-006"


@dataclass(frozen=True, slots=True)
class ParseIssue:
    code: str
    message: str
    requirement: str
    path: Path
    lineno: int
    col: int | None = None
    suggestion: str | None = None

    def to_finding(
        self,
        excerpt: str | None = None,
        context: tuple[str, ...] = (),
    ) -> Finding:
        return Finding(
            rule_id=self.code,
            clause=NO_CLAUSE,
            severity=Severity.INFO,
            message=self.message,
            requirement=self.requirement,
            path=self.path,
            lineno=self.lineno,
            col=self.col,
            excerpt=excerpt,
            context=context,
            suggestion=self.suggestion,
        )
