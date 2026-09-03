"""Профиль — адаптация набора правил под требования конкретной кафедры."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from nk.core.finding import Severity

#: ``Any`` — параметры приходят из TOML, их типы определяет автор правила, а не ядро.
ParamValue = Any
Params = Mapping[str, ParamValue]


@dataclass(frozen=True, slots=True)
class Profile:
    """Разрешённый профиль: отключения, переопределения уровней и параметры правил.

    Разрешённый — значит, что значения по умолчанию из объявлений правил уже слиты
    с переопределениями из TOML. Строится через :meth:`resolve`.
    """

    name: str = "base"
    disabled: frozenset[str] = frozenset()
    severities: Mapping[str, Severity] = field(default_factory=dict)
    params: Mapping[str, Params] = field(default_factory=dict)

    def is_disabled(self, rule_id: str) -> bool:
        return rule_id in self.disabled

    def severity_for(self, rule_id: str, default: Severity) -> Severity:
        return self.severities.get(rule_id, default)

    def params_for(self, rule_id: str) -> Params:
        return self.params.get(rule_id, {})

    def resolve(self, defaults: Mapping[str, Params]) -> "Profile":
        """Слить значения по умолчанию из объявлений правил с переопределениями профиля."""
        merged: dict[str, Params] = {}
        for rule_id in defaults.keys() | self.params.keys():
            merged[rule_id] = {**defaults.get(rule_id, {}), **self.params.get(rule_id, {})}
        return Profile(
            name=self.name,
            disabled=self.disabled,
            severities=self.severities,
            params=merged,
        )
