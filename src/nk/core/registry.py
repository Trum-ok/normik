"""Обход пакета правил, загрузка и фильтрация.

Правила регистрируются побочным эффектом импорта: декоратор :func:`~nk.core.rule.rule`
кладёт правило в глобальный реестр.

Запустится правило или нет, решают пять независимых причин: ключи ``--select``
и ``--ignore``, ``disable`` и ``enable`` профиля, стандарт прогона и пометка
``default_off`` в объявлении. Решение принимается в одном месте — :func:`decide` —
и возвращает не только ответ, но и причину: без неё «отключено» в выводе
означает пять разных вещей сразу.
"""

import importlib
import pkgutil
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from nk.core.categories import BY_NAME, PACKAGE, UnknownCategoryError
from nk.core.diagnostics import INTERNAL
from nk.core.profile import Profile, ProfileError
from nk.core.rule import REGISTRY, RuleImpl, RuleRegistry, UnknownRuleError

RULES_PACKAGE = PACKAGE


def load_rules(package: str = RULES_PACKAGE, registry: RuleRegistry | None = None) -> RuleRegistry:
    """Импортировать все модули пакета правил и вернуть заполненный реестр."""
    root = importlib.import_module(package)
    for module in pkgutil.walk_packages(root.__path__, prefix=f"{package}."):
        if module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        importlib.import_module(module.name)
    # Явное сравнение с None: пустой реестр ложен из-за __len__.
    loaded = REGISTRY if registry is None else registry
    _require_categories(loaded)
    return loaded


def _require_categories(registry: RuleRegistry) -> None:
    """Каталог правила обязан быть объявленной категорией.

    Иначе правило, положенное мимо категории, выпало бы из документации молча.
    """
    misplaced = sorted(
        f"{impl.id} ({impl.module})"
        for impl in registry.all()
        if impl.module.startswith(f"{PACKAGE}.") and impl.category not in BY_NAME
    )
    if misplaced:
        allowed = ", ".join(BY_NAME)
        raise UnknownCategoryError(
            f"правила лежат вне категорий: {misplaced}; допустимые каталоги: {allowed}"
        )


class Reason(StrEnum):
    """Почему правило запускается или нет.

    Значения перечисления — часть контракта между ядром и выводом; как причина
    называется по-русски, знает :data:`REASON_LABELS`.
    """

    ACTIVE = "active"
    """Правило применимо и ничем не выключено."""

    SELECTED = "selected"
    """Перечислено ключом ``--select``: он сильнее стандарта и ``default_off``."""

    ENABLED = "enabled"
    """Включено профилем ключом ``enable`` вопреки стандарту или ``default_off``."""

    NOT_SELECTED = "not-selected"
    """Ключ ``--select`` задан, и этого правила в нём нет."""

    IGNORED = "ignored"
    """Исключено ключом ``--ignore``."""

    DISABLED = "disabled"
    """Отключено профилем ключом ``disable``."""

    OTHER_STANDARD = "other-standard"
    """Требования нет ни в активном стандарте, ни в привлечённых им."""

    DEFAULT_OFF = "default-off"
    """Выключено в объявлении правила и не включено ни профилем, ни ключом."""


#: Как причина называется в выводе. Коротко: это ячейка таблицы, а не объяснение.
REASON_LABELS: dict[Reason, str] = {
    Reason.ACTIVE: "включено",
    Reason.SELECTED: "выбрано ключом",
    Reason.ENABLED: "включено профилем",
    Reason.NOT_SELECTED: "не выбрано",
    Reason.IGNORED: "исключено ключом",
    Reason.DISABLED: "отключено профилем",
    Reason.OTHER_STANDARD: "нет в стандарте",
    Reason.DEFAULT_OFF: "выключено по умолчанию",
}


@dataclass(frozen=True, slots=True)
class Decision:
    """Запускается ли правило и почему именно так."""

    rule: RuleImpl
    reason: Reason

    @property
    def enabled(self) -> bool:
        return self.reason in _ENABLING

    @property
    def label(self) -> str:
        return REASON_LABELS[self.reason]


#: Причины, при которых правило запускается.
_ENABLING = frozenset({Reason.ACTIVE, Reason.SELECTED, Reason.ENABLED})


def decide(
    impl: RuleImpl,
    *,
    profile: Profile | None = None,
    select: frozenset[str] | None = None,
    ignore: frozenset[str] = frozenset(),
) -> Decision:
    """Решить судьбу одного правила и назвать причину.

    Порядок причин — от сильной к слабой. ``--select`` задаёт стартовый набор
    и перекрывает и стандарт, и ``default_off``: правило запрашивают по имени,
    зная, что делают. Отключения сильнее включений: ``--ignore`` и ``disable``
    вычитаются даже из того, что названо ключом.

    ``select`` и ``ignore`` — уже развёрнутые нынешние идентификаторы,
    см. :func:`select_rules`.
    """
    if select is not None and impl.id not in select:
        return Decision(impl, Reason.NOT_SELECTED)
    if impl.id in ignore:
        return Decision(impl, Reason.IGNORED)
    if profile is not None and profile.is_disabled(impl.id):
        return Decision(impl, Reason.DISABLED)
    if select is not None:
        return Decision(impl, Reason.SELECTED)
    # Ключ ``enable`` в профиле сильнее и стандарта, и пометки в объявлении: им
    # подключают требование из другого стандарта, если так велит положение вуза.
    if profile is not None and profile.is_enabled(impl.id):
        return Decision(impl, Reason.ENABLED if _held_back(impl, profile) else Reason.ACTIVE)
    # Без профиля стандарт не выбран, и применимо всё: пункты сужают набор только
    # тогда, когда есть с чем сверяться.
    if profile is not None and not impl.applies_under(*profile.active):
        return Decision(impl, Reason.OTHER_STANDARD)
    if impl.default_off:
        return Decision(impl, Reason.DEFAULT_OFF)
    return Decision(impl, Reason.ACTIVE)


def _held_back(impl: RuleImpl, profile: Profile) -> bool:
    """Понадобился ли ключ ``enable``: без него правило бы не запустилось.

    Профиль перечисляет в ``enable`` и то, что и так работает, — от этого
    ничего не меняется, но и «включено профилем» о таком правиле сказать нельзя.
    """
    return impl.default_off or not impl.applies_under(*profile.active)


def review(
    registry: RuleRegistry,
    *,
    profile: Profile | None = None,
    select: Iterable[str] | None = None,
    ignore: Iterable[str] | None = None,
) -> tuple[Decision, ...]:
    """Решение по каждому правилу реестра, в порядке идентификаторов.

    Неизвестный идентификатор в ключах — ошибка, иначе опечатка молча выключает
    проверку. Прежние имена правил разворачиваются в нынешние: профиль кафедры
    и командная строка переживают переименование.
    """
    chosen = None if select is None else frozenset(_canonical(registry, select))
    excluded = frozenset(_canonical(registry, ignore or ()))
    return tuple(decide(impl, profile=profile, select=chosen, ignore=excluded) for impl in registry)


def select_rules(
    registry: RuleRegistry,
    *,
    profile: Profile | None = None,
    select: Iterable[str] | None = None,
    ignore: Iterable[str] | None = None,
) -> tuple[RuleImpl, ...]:
    """Отобрать правила к запуску — те же решения, только без причин."""
    return tuple(
        decision.rule
        for decision in review(registry, profile=profile, select=select, ignore=ignore)
        if decision.enabled
    )


def _canonical(registry: RuleRegistry, ids: Iterable[str]) -> list[str]:
    return [_require(registry, rule_id).id for rule_id in ids]


def partition_ids(values: Iterable[str] | None) -> tuple[list[str] | None, frozenset[str]]:
    """Разделить перечень идентификаторов на правила и внутренние диагностики."""
    if values is None:
        return None, frozenset()
    listed = list(values)
    return (
        [item for item in listed if item not in INTERNAL],
        frozenset(item for item in listed if item in INTERNAL),
    )


def _require(registry: RuleRegistry, rule_id: str) -> RuleImpl:
    try:
        return registry.get(rule_id)
    except UnknownRuleError:
        raise UnknownRuleError(f"неизвестное правило {rule_id!r}") from None


def validate_profile(profile: Profile, registry: RuleRegistry) -> None:
    """Проверить, что профиль ссылается на существующие правила.

    Опечатка в идентификаторе иначе молча выключает проверку или теряет параметр.
    """
    unknown = sorted(
        rule_id
        for rule_id in profile.mentioned_rules()
        if rule_id not in registry and rule_id not in INTERNAL
    )
    if unknown:
        raise ProfileError(
            f"профиль {profile.origin!r} ссылается на неизвестные правила: {unknown}"
        )
