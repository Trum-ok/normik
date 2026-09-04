"""Профиль — адаптация набора правил под требования конкретной кафедры.

Основной механизм расширяемости: кафедра правит профиль, а не форкает репозиторий.
"""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from nk.core.elements import STRUCTURAL_ELEMENTS, normalize_element
from nk.core.finding import Severity

#: ``Any`` — параметры приходят из TOML, их типы определяет автор правила, а не ядро.
ParamValue = Any
Params = Mapping[str, ParamValue]

BUILTIN_PACKAGE = "nk.profiles"
DEFAULT_PROFILE = "base"
PROFILE_SUFFIX = ".toml"

_TOP_LEVEL_KEYS = frozenset({"name", "extends", "disable", "enable", "rules", "elements"})
_RULE_KEYS = frozenset({"severity", "params"})
_ELEMENT_KEYS = frozenset({"aliases"})


class ProfileError(ValueError):
    """Профиль не читается или содержит недопустимые значения."""


@dataclass(frozen=True, slots=True)
class Profile:
    """Разрешённый профиль: отключения, переопределения уровней и параметры правил.

    Разрешённый — значит, что значения по умолчанию из объявлений правил уже слиты
    с переопределениями из TOML. Строится через :meth:`resolve`.
    """

    name: str = "base"
    disabled: frozenset[str] = frozenset()
    enabled: frozenset[str] = frozenset()
    """Правила, выключенные по умолчанию, но нужные этой кафедре."""

    severities: Mapping[str, Severity] = field(default_factory=dict)
    params: Mapping[str, Params] = field(default_factory=dict)
    element_aliases: Mapping[str, str] = field(default_factory=dict)
    """Наименования структурных элементов кафедры и канонические наименования стандарта."""

    def is_disabled(self, rule_id: str) -> bool:
        return rule_id in self.disabled

    def is_enabled(self, rule_id: str) -> bool:
        """Включено ли профилем правило, выключенное по умолчанию."""
        return rule_id in self.enabled

    def severity_for(self, rule_id: str, default: Severity) -> Severity:
        return self.severities.get(rule_id, default)

    def params_for(self, rule_id: str) -> Params:
        return self.params.get(rule_id, {})

    def mentioned_rules(self) -> frozenset[str]:
        """Правила, названные профилем явно — для проверки на опечатки в идентификаторах."""
        return frozenset(self.disabled | self.enabled | self.severities.keys() | self.params.keys())

    def resolve(self, defaults: Mapping[str, Params]) -> "Profile":
        """Слить значения по умолчанию из объявлений правил с переопределениями профиля."""
        merged: dict[str, Params] = {}
        for rule_id in defaults.keys() | self.params.keys():
            merged[rule_id] = {**defaults.get(rule_id, {}), **self.params.get(rule_id, {})}
        return Profile(
            name=self.name,
            disabled=self.disabled,
            enabled=self.enabled,
            severities=self.severities,
            params=merged,
            element_aliases=self.element_aliases,
        )


def load_profile(source: str | Path | None = None) -> Profile:
    """Прочитать профиль по имени встроенного либо по пути к файлу.

    ``extends`` — один уровень: профиль, от которого наследуются, сам наследоваться
    не может. Это исключает циклы без отдельной проверки.
    """
    child_path, child = _read(source if source is not None else DEFAULT_PROFILE)
    parent_ref = child.get("extends")
    if parent_ref is None:
        return _build(child)

    _, parent = _read(parent_ref, relative_to=child_path)
    if parent.get("extends") is not None:
        raise ProfileError(
            f"профиль {parent_ref!r} сам наследуется от другого: наследование только на один уровень"
        )
    return _build(_merge(parent, child))


def _read(
    source: str | Path, relative_to: Path | None = None
) -> tuple[Path | None, dict[str, Any]]:
    path = _locate(source, relative_to)
    if path is None:
        text = _builtin_text(str(source))
        return None, _parse(text, str(source))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ProfileError(f"не удалось прочитать профиль {path}: {error}") from error
    return path, _parse(text, str(path))


def _locate(source: str | Path, relative_to: Path | None) -> Path | None:
    candidate = Path(source)
    if candidate.is_file():
        return candidate
    if relative_to is not None:
        for name in (candidate, candidate.with_suffix(PROFILE_SUFFIX)):
            nearby = relative_to.parent / name
            if nearby.is_file():
                return nearby
    return None


def _builtin_text(name: str) -> str:
    resource = resources.files(BUILTIN_PACKAGE).joinpath(f"{name}{PROFILE_SUFFIX}")
    if not resource.is_file():
        raise ProfileError(f"профиль {name!r} не найден ни среди встроенных, ни как файл")
    return resource.read_text(encoding="utf-8")


def _parse(text: str, origin: str) -> dict[str, Any]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ProfileError(f"профиль {origin}: {error}") from error

    unknown = data.keys() - _TOP_LEVEL_KEYS
    if unknown:
        raise ProfileError(f"профиль {origin}: неизвестные ключи {sorted(unknown)}")
    for rule_id, section in data.get("rules", {}).items():
        if not isinstance(section, dict):
            raise ProfileError(f"профиль {origin}: секция [rules.{rule_id!r}] должна быть таблицей")
        extra = section.keys() - _RULE_KEYS
        if extra:
            raise ProfileError(
                f"профиль {origin}: правило {rule_id!r}, неизвестные ключи {sorted(extra)}"
            )

    elements = data.get("elements", {})
    if not isinstance(elements, dict):
        raise ProfileError(f"профиль {origin}: секция [elements] должна быть таблицей")
    unknown_elements = elements.keys() - _ELEMENT_KEYS
    if unknown_elements:
        raise ProfileError(
            f"профиль {origin}: [elements], неизвестные ключи {sorted(unknown_elements)}"
        )
    return data


def _merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    rules: dict[str, Any] = {}
    parent_rules = parent.get("rules", {})
    child_rules = child.get("rules", {})
    for rule_id in parent_rules.keys() | child_rules.keys():
        base = parent_rules.get(rule_id, {})
        over = child_rules.get(rule_id, {})
        rules[rule_id] = {
            **base,
            **over,
            "params": {**base.get("params", {}), **over.get("params", {})},
        }
    return {
        "name": child.get("name", parent.get("name")),
        "disable": [*parent.get("disable", []), *child.get("disable", [])],
        "enable": [*parent.get("enable", []), *child.get("enable", [])],
        "rules": rules,
        "elements": {
            "aliases": {
                **parent.get("elements", {}).get("aliases", {}),
                **child.get("elements", {}).get("aliases", {}),
            }
        },
    }


def _build(data: dict[str, Any]) -> Profile:
    severities: dict[str, Severity] = {}
    params: dict[str, Params] = {}
    for rule_id, section in data.get("rules", {}).items():
        raw = section.get("severity")
        if raw is not None:
            severities[rule_id] = _severity(raw, rule_id)
        rule_params = section.get("params")
        if rule_params:
            params[rule_id] = rule_params

    return Profile(
        name=str(data.get("name") or DEFAULT_PROFILE),
        disabled=frozenset(data.get("disable", [])),
        enabled=frozenset(data.get("enable", [])),
        severities=severities,
        params=params,
        element_aliases=_aliases(data.get("elements", {}).get("aliases", {})),
    )


def _aliases(raw: object) -> dict[str, str]:
    """Синонимы наименований: как называет элемент кафедра — как называет стандарт.

    Наименование справа проверяется по стандарту: опечатка в нём иначе завела бы
    синоним в никуда, и элемент молча перестал бы опознаваться.
    """
    if not isinstance(raw, dict):
        raise ProfileError("профиль: [elements.aliases] должна быть таблицей")
    found: dict[str, str] = {}
    for name, canonical in raw.items():
        target = normalize_element(str(canonical))
        if target not in STRUCTURAL_ELEMENTS:
            allowed = ", ".join(sorted(STRUCTURAL_ELEMENTS))
            raise ProfileError(
                f"синоним {name!r}: {canonical!r} не структурный элемент, допустимы: {allowed}"
            )
        found[normalize_element(str(name))] = target
    return found


def _severity(raw: object, rule_id: str) -> Severity:
    try:
        return Severity(raw)
    except ValueError:
        allowed = ", ".join(level.value for level in Severity)
        raise ProfileError(
            f"правило {rule_id!r}: недопустимый уровень {raw!r}, допустимы: {allowed}"
        ) from None
