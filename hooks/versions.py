"""Подстановка в документацию того, что объявлено в коде.

Версии, пороги и перечень внутренних диагностик живут в одном месте — в
пакете; в тексте документации они записываются плейсхолдерами и подставляются
при сборке сайта. Иначе документация расходится с действительностью на первом
же изменении.
"""

import re
import tomllib
from pathlib import Path
from typing import Any

from nk import __version__
from nk.core import categories, standards
from nk.core.diagnostics import INTERNAL
from nk.core.registry import load_rules
from nk.report.agent import DEFAULT_LIMIT
from nk.report.json import SCHEMA_VERSION as JSON_SCHEMA_VERSION

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _python_requires() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["requires-python"]).lstrip(">=~^ ")


def _diagnostics_table() -> str:
    rows = [
        f"| `{item.code}` | `{item.severity.value}` | {item.title} |" for item in INTERNAL.values()
    ]
    return "\n".join(["| Код | Уровень | Когда |", "|---|---|---|", *rows])


def _categories_table() -> str:
    rules = load_rules()
    rows = []
    for category in categories.CATEGORIES:
        count = sum(1 for impl in rules if impl.category == category.name)
        if count:
            rows.append(f"| {category.title} | {count} |")
    return "\n".join(["| Что регулируется | Правил |", "|---|---|", *rows])


def _standards_table() -> str:
    """Стандарты, которые профиль вправе назвать активным."""
    rows = [
        f"| `{item.id}` | {item.title}{', по умолчанию' if item is standards.DEFAULT else ''} |"
        for item in standards.STANDARDS.values()
        if not item.referenced
    ]
    return "\n".join(["| Значение | Стандарт |", "|---|---|", *rows])


def _references_table() -> str:
    """Стандарты, которые активными не бывают: их только привлекают."""
    rows = [
        f"| `{item.id}` | {item.title} |"
        for item in standards.STANDARDS.values()
        if item.referenced
    ]
    return "\n".join(["| Значение | Стандарт |", "|---|---|", *rows])


def _standards_list() -> str:
    titles = [item.title for item in standards.STANDARDS.values() if not item.referenced]
    if len(titles) == 1:
        return titles[0]
    return f"{', '.join(titles[:-1])} и {titles[-1]}"


VALUES = {
    "nk_version": __version__,
    "json_schema_version": JSON_SCHEMA_VERSION,
    "python_requires": _python_requires(),
    "agent_limit": str(DEFAULT_LIMIT),
    "diagnostics_table": _diagnostics_table(),
    "standards_table": _standards_table(),
    "references_table": _references_table(),
    "standards_list": _standards_list(),
    "standards_default": standards.DEFAULT.title,
    "categories_table": _categories_table(),
}

# Имя плейсхолдера — только известное: `{{` в примерах LaTeX и Python под
# замену не попадает.
PLACEHOLDER = re.compile(r"\{\{\s*(" + "|".join(VALUES) + r")\s*\}\}")


def on_page_markdown(markdown: str, **_: Any) -> str:
    return PLACEHOLDER.sub(lambda match: VALUES[match.group(1)], markdown)
