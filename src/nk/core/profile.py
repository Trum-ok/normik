"""Профиль — адаптация набора правил под требования конкретной кафедры.

Основной механизм расширяемости: кафедра правит профиль, а не форкает репозиторий.
"""

import os
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from nk.core.elements import DEFAULT_ELEMENTS, ROLES, Elements, ElementsError, normalize_element
from nk.core.finding import Severity
from nk.core.headings import DEFAULT_APPENDIX_LETTERS

#: ``Any`` — параметры приходят из TOML, их типы определяет автор правила, а не ядро.
ParamValue = Any
Params = Mapping[str, ParamValue]

BUILTIN_PACKAGE = "nk.profiles"
DEFAULT_PROFILE = "base"
PROFILE_SUFFIX = ".toml"

PYPROJECT = "pyproject.toml"
PYPROJECT_SECTION = "tool.nk"

#: Имена конфигурационных файлов в порядке предпочтения внутри одного каталога.
CONFIG_NAMES = ("nk.toml", ".nk.toml", PYPROJECT)

_TOP_LEVEL_KEYS = frozenset(
    {"name", "extends", "disable", "enable", "rules", "elements", "appendix"}
)
_RULE_KEYS = frozenset({"severity", "params"})
_ELEMENT_KEYS = frozenset({"aliases", "order", "roles"})
_APPENDIX_KEYS = frozenset({"letters"})


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
    elements: Elements = DEFAULT_ELEMENTS
    """Словарь структурных элементов: состав, порядок, роли и синонимы кафедры."""

    appendix_letters: str = DEFAULT_APPENDIX_LETTERS
    """Обозначения приложений по порядку: каждый знак строки — одно обозначение."""

    source: Path | None = None
    """Файл, из которого прочитан профиль; ``None`` — встроенный."""

    @property
    def origin(self) -> str:
        """Как называть профиль в сообщениях: файл точнее имени, которого может и не быть."""
        return str(self.source) if self.source is not None else self.name

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
            elements=self.elements,
            appendix_letters=self.appendix_letters,
            source=self.source,
        )


def load_profile(
    source: str | Path | None = None, *, search_from: Sequence[Path] | None = None
) -> Profile:
    """Прочитать профиль по имени встроенного либо по пути к файлу.

    Без явного источника профиль ищется по дереву каталогов (``search_from``), а если
    не найден — берётся встроенный ``base``.

    ``extends`` — один уровень: профиль, от которого наследуются, сам наследоваться
    не может. Это исключает циклы без отдельной проверки.
    """
    if source is None:
        found = discover(search_from) if search_from is not None else None
        source = found if found is not None else DEFAULT_PROFILE

    child_path, child = _read(source)
    parent_ref = child.get("extends")
    if parent_ref is None:
        return _build(child, child_path)

    _, parent = _read(parent_ref, relative_to=child_path)
    if parent.get("extends") is not None:
        raise ProfileError(
            f"профиль {parent_ref!r} сам наследуется от другого: наследование только на один уровень"
        )
    return _build(_merge(parent, child), child_path)


def discover(paths: Sequence[Path]) -> Path | None:
    """Ближайший файл конфигурации вверх по дереву от проверяемых путей.

    Поиск начинается с общего каталога всех путей: профиль на прогон один, поэтому
    и файл ищется один — иначе части исходников проверялись бы по разным правилам.
    ``pyproject.toml`` без секции ``[tool.nk]`` не считается конфигурацией: подъём
    продолжается выше.
    """
    root = _common_root(paths)
    for directory in [root, *root.parents]:
        for name in CONFIG_NAMES:
            candidate = directory / name
            if candidate.is_file() and (name != PYPROJECT or _has_section(candidate)):
                return candidate
    return None


def _common_root(paths: Sequence[Path]) -> Path:
    directories = [path if path.is_dir() else path.parent for path in paths]
    resolved = [str(directory.resolve()) for directory in directories]
    if not resolved:
        return Path.cwd().resolve()
    return Path(os.path.commonpath(resolved))


def _has_section(path: Path) -> bool:
    """Есть ли в ``pyproject.toml`` секция ``[tool.nk]``.

    Недоступный файл не ошибка профиля: поиск идёт дальше вверх. А вот битый TOML
    разбирается как ошибка — в нём могла быть настройка кафедры, и молчаливый
    пропуск выключил бы её незаметно.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ProfileError(f"профиль {path}: {error}") from error
    tool = data.get("tool")
    return isinstance(tool, dict) and isinstance(tool.get("nk"), dict)


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
    return path, _parse(text, str(path), section=path.name == PYPROJECT)


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


def _parse(text: str, origin: str, section: bool = False) -> dict[str, Any]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ProfileError(f"профиль {origin}: {error}") from error
    if section:
        data = _section(data, origin)

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

    appendix = data.get("appendix", {})
    if not isinstance(appendix, dict):
        raise ProfileError(f"профиль {origin}: секция [appendix] должна быть таблицей")
    unknown_appendix = appendix.keys() - _APPENDIX_KEYS
    if unknown_appendix:
        raise ProfileError(
            f"профиль {origin}: [appendix], неизвестные ключи {sorted(unknown_appendix)}"
        )
    return data


def _section(data: dict[str, Any], origin: str) -> dict[str, Any]:
    """Профиль внутри ``pyproject.toml`` — секция ``[tool.nk]``."""
    tool = data.get("tool", {})
    found = tool.get("nk") if isinstance(tool, dict) else None
    if found is None:
        raise ProfileError(f"профиль {origin}: нет секции [{PYPROJECT_SECTION}]")
    if not isinstance(found, dict):
        raise ProfileError(f"профиль {origin}: секция [{PYPROJECT_SECTION}] должна быть таблицей")
    return found


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
        "elements": _merge_elements(parent.get("elements", {}), child.get("elements", {})),
        "appendix": {**parent.get("appendix", {}), **child.get("appendix", {})},
    }


def _merge_elements(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Слить секции ``[elements]`` родителя и наследника.

    Синонимы складываются: кафедра дописывает свои наименования к чужим. Состав
    и роли — нет: наследник, объявивший ``order``, задаёт словарь целиком.
    Частичное слияние состава давало бы профиль, в котором остались элементы
    источника, от которого уходили.
    """
    own = "order" in child or "roles" in child
    base = child if own else parent
    merged: dict[str, Any] = {key: value for key, value in base.items() if key != "aliases"}
    merged["aliases"] = {**parent.get("aliases", {}), **child.get("aliases", {})}
    return merged


def _build(data: dict[str, Any], source: Path | None = None) -> Profile:
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
        elements=_elements(data.get("elements", {})),
        appendix_letters=_appendix_letters(data.get("appendix", {})),
        source=source,
    )


def _elements(raw: dict[str, Any]) -> Elements:
    """Собрать словарь структурных элементов из секции ``[elements]``.

    Без ``order`` берётся состав по умолчанию: профиль кафедры правит наименования,
    а не перечень элементов.

    Без ``roles`` роли тоже берутся по умолчанию, но только те их наименования,
    которые остались в составе: у источника требований, где нет реферата, роль
    реферата пустует, и правила о реферате молчат.
    """
    order = _order(raw["order"]) if "order" in raw else DEFAULT_ELEMENTS.order
    roles = _roles(raw["roles"]) if "roles" in raw else _kept_roles(order)
    try:
        return Elements(order=order, roles=roles, aliases=_aliases(raw.get("aliases", {}), order))
    except ElementsError as error:
        raise ProfileError(f"профиль: [elements] {error}") from error


def _appendix_letters(raw: dict[str, Any]) -> str:
    """Обозначения приложений: знаки строки по порядку — А, Б, В либо A, B, C.

    Повтор знака запрещён: по обозначению определяется место приложения
    в последовательности, а у повторённого знака мест было бы два.
    """
    if "letters" not in raw:
        return DEFAULT_APPENDIX_LETTERS
    letters = raw["letters"]
    if not isinstance(letters, str):
        raise ProfileError("профиль: [appendix] letters должен быть строкой обозначений")
    stripped = "".join(letters.split())
    if not stripped:
        raise ProfileError("профиль: [appendix] letters пуст, обозначать приложения нечем")
    repeated = sorted({letter for letter in stripped if stripped.count(letter) > 1})
    if repeated:
        raise ProfileError(f"профиль: [appendix] letters, знаки повторяются: {repeated}")
    return stripped


def _kept_roles(order: Mapping[str, int]) -> dict[str, frozenset[str]]:
    """Роли по умолчанию, суженные до наименований, которые есть в составе."""
    return {role: names & order.keys() for role, names in DEFAULT_ELEMENTS.roles.items() if names}


def _order(raw: object) -> dict[str, int]:
    """Состав и порядок: наименование и его ранг.

    Ранг общий у элементов, которые занимают одно место и заменяют друг друга —
    например у отдельного перечня терминов и объединённого перечня.
    """
    if not isinstance(raw, dict):
        raise ProfileError("профиль: [elements.order] должна быть таблицей наименований и рангов")
    found: dict[str, int] = {}
    for name, rank in raw.items():
        if not isinstance(rank, int) or isinstance(rank, bool):
            raise ProfileError(f"профиль: ранг элемента {name!r} должен быть целым, а не {rank!r}")
        found[normalize_element(str(name))] = rank
    if not found:
        raise ProfileError("профиль: [elements.order] пуста, состав элементов задавать нечем")
    return found


def _roles(raw: object) -> dict[str, frozenset[str]]:
    """Роли элементов: правила спрашивают словарь по роли, а не по наименованию."""
    if not isinstance(raw, dict):
        raise ProfileError("профиль: [elements.roles] должна быть таблицей")
    unknown = raw.keys() - ROLES
    if unknown:
        allowed = ", ".join(sorted(ROLES))
        raise ProfileError(f"профиль: неизвестные роли {sorted(unknown)}, допустимы: {allowed}")
    found: dict[str, frozenset[str]] = {}
    for role, names in raw.items():
        if not isinstance(names, list):
            raise ProfileError(f"профиль: роль {role!r} должна быть списком наименований")
        found[role] = frozenset(normalize_element(str(name)) for name in names)
    return found


def _aliases(raw: object, order: Mapping[str, int]) -> dict[str, str]:
    """Синонимы наименований: как называет элемент кафедра — как называет источник.

    Наименование справа проверяется по составу: опечатка в нём иначе завела бы
    синоним в никуда, и элемент молча перестал бы опознаваться.
    """
    if not isinstance(raw, dict):
        raise ProfileError("профиль: [elements.aliases] должна быть таблицей")
    found: dict[str, str] = {}
    for name, canonical in raw.items():
        target = normalize_element(str(canonical))
        if target not in order:
            allowed = ", ".join(sorted(order))
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
