"""Обход пакета правил, загрузка и фильтрация.

Правила регистрируются побочным эффектом импорта: декоратор :func:`~nk.core.rule.rule`
кладёт правило в глобальный реестр.
"""

import importlib
import pkgutil
from collections.abc import Iterable

from nk.core.profile import Profile
from nk.core.rule import REGISTRY, RuleImpl, RuleRegistry, UnknownRuleError

RULES_PACKAGE = "nk.rules"


def load_rules(package: str = RULES_PACKAGE, registry: RuleRegistry | None = None) -> RuleRegistry:
    """Импортировать все модули пакета правил и вернуть заполненный реестр."""
    root = importlib.import_module(package)
    for module in pkgutil.walk_packages(root.__path__, prefix=f"{package}."):
        if module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        importlib.import_module(module.name)
    # Явное сравнение с None: пустой реестр ложен из-за __len__.
    return REGISTRY if registry is None else registry


def select_rules(
    registry: RuleRegistry,
    *,
    profile: Profile | None = None,
    select: Iterable[str] | None = None,
    ignore: Iterable[str] | None = None,
) -> tuple[RuleImpl, ...]:
    """Отобрать правила к запуску.

    ``select`` задаёт стартовый набор, затем из него вычитаются отключённые
    профилем и перечисленные в ``ignore``. Неизвестный идентификатор — ошибка,
    иначе опечатка молча выключает проверку.
    """
    if select is None:
        chosen = list(registry.all())
    else:
        chosen = [_require(registry, rule_id) for rule_id in select]

    excluded: set[str] = set()
    if ignore is not None:
        excluded.update(_require(registry, rule_id).id for rule_id in ignore)
    if profile is not None:
        excluded.update(impl.id for impl in chosen if profile.is_disabled(impl.id))

    return tuple(sorted((impl for impl in chosen if impl.id not in excluded), key=lambda r: r.id))


def _require(registry: RuleRegistry, rule_id: str) -> RuleImpl:
    try:
        return registry.get(rule_id)
    except UnknownRuleError:
        raise UnknownRuleError(f"неизвестное правило {rule_id!r}") from None
