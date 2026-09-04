"""Замечания парсера.

Битый или непонятый TeX не роняет запуск: парсер сообщает о таких участках
находками уровня ``info`` и продолжает работу.
"""

from dataclasses import dataclass
from pathlib import Path

from nk.core.diagnostics import (
    ENCODING_FALLBACK,
    ENVIRONMENT_ORPHAN_END,
    ENVIRONMENT_UNCLOSED,
    GROUP_UNCLOSED,
    INPUT_CYCLE,
    INPUT_MISSING,
    NO_CLAUSE,
)
from nk.core.finding import Finding, Severity

__all__ = [
    "ENCODING_FALLBACK",
    "ENVIRONMENT_ORPHAN_END",
    "ENVIRONMENT_UNCLOSED",
    "GROUP_UNCLOSED",
    "INPUT_CYCLE",
    "INPUT_MISSING",
    "NO_CLAUSE",
    "ParseIssue",
]


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
