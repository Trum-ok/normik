"""Замечания парсера.

Битый или непонятый TeX не роняет запуск: парсер сообщает о таких участках
находкой и продолжает работу. Уровень находки объявлен вместе с самой
диагностикой в :mod:`nk.core.diagnostics`.
"""

from dataclasses import dataclass
from pathlib import Path

from nk.core import diagnostics
from nk.core.finding import Finding


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
        return diagnostics.to_finding(
            self.code,
            message=self.message,
            requirement=self.requirement,
            path=self.path,
            lineno=self.lineno,
            col=self.col,
            suggestion=self.suggestion,
            excerpt=excerpt,
            context=context,
        )
