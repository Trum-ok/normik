"""Подавление отдельных находок директивами в исходниках.

Линтер внедряют на готовую работу, где нарушений сотни. Без возможности заглушить
конкретное место его просто перестанут запускать.

Разбор комментариев — в :mod:`nk.parse.suppressions`; здесь только модель.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from nk.core.finding import Finding

Scope = Literal["line", "file"]


@dataclass(frozen=True, slots=True)
class Suppression:
    path: Path
    lineno: int
    scope: Scope
    rule_ids: frozenset[str] = frozenset()
    """Пустое множество — подавляются все правила."""

    reason: str = ""

    def covers(self, finding: Finding) -> bool:
        if finding.path != self.path:
            return False
        if self.scope == "line" and finding.lineno != self.lineno:
            return False
        return not self.rule_ids or finding.rule_id in self.rule_ids


@dataclass(frozen=True, slots=True)
class Suppressions:
    items: tuple[Suppression, ...] = ()
    used: set[int] = field(default_factory=set, compare=False, repr=False)
    """Индексы сработавших директив — по ним находятся подавления, ставшие лишними."""

    def match(self, finding: Finding) -> Suppression | None:
        """Найти директиву, подавляющую находку, и отметить её сработавшей."""
        for index, item in enumerate(self.items):
            if item.covers(finding):
                self.used.add(index)
                return item
        return None

    def renamed(self, aliases: Mapping[str, str]) -> "Suppressions":
        """Развернуть прежние идентификаторы правил в нынешние.

        Директива с прежним именем написана в чужом отчёте и обязана продолжать
        работать: иначе переименование правила молча включило бы проверку обратно.
        """
        if not aliases:
            return self
        return Suppressions(
            items=tuple(
                replace(item, rule_ids=frozenset(aliases.get(name, name) for name in item.rule_ids))
                for item in self.items
            ),
            used=self.used,
        )

    def unused(self) -> list[Suppression]:
        return [item for index, item in enumerate(self.items) if index not in self.used]
