"""Генератор страниц документации по правилам.

На каждое правило — своя страница; сводка и оглавление собираются из реестра.
Файлы в `docs/rules/` создаются командой `nk rules docs` и руками не редактируются.
"""

from collections.abc import Iterable
from pathlib import Path

from nk.core import categories, standards
from nk.core.finding import Severity
from nk.core.rule import RuleImpl
from nk.report import examples

INDEX_PAGE = "index.md"
SUMMARY_PAGE = "SUMMARY.md"

INDEX_HEADER = """\
# Правила

Проверяются только исходники `.tex`. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

Правила разложены по тому, что они регулируют, а не по разделам стандарта:
у разных стандартов разделы разные, а иллюстрации остаются иллюстрациями.

Уровень {error} влияет на код возврата, {warning} и {info} — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).
"""

#: Пунктов нет: требование не записано ни в одном поддерживаемом стандарте.
NO_CLAUSE_LABEL = "—"

#: Стандарты в ячейке таблицы: по одному на строку.
CLAUSE_SEPARATOR = "<br>"


def render_pages(rules: Iterable[RuleImpl], *, fixtures_root: Path | None = None) -> dict[str, str]:
    """Все страницы раздела: имя файла — содержимое."""
    ordered = _ordered(rules)
    pages = {
        INDEX_PAGE: render_index(ordered),
        SUMMARY_PAGE: render_summary(ordered),
    }
    for impl in ordered:
        pages[f"{impl.id}.md"] = render_rule(impl, fixtures_root=fixtures_root)
    return pages


def write_pages(
    rules: Iterable[RuleImpl], directory: Path, *, fixtures_root: Path | None = None
) -> tuple[int, int]:
    """Записать страницы в каталог, удалив оставшиеся от снятых правил.

    Возвращает число записанных и число удалённых файлов.
    """
    pages = render_pages(rules, fixtures_root=fixtures_root)
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in pages.items():
        (directory / name).write_text(text, encoding="utf-8")

    removed = 0
    for path in sorted(directory.glob("*.md")):
        if path.name not in pages:
            path.unlink()
            removed += 1
    return len(pages), removed


def render_index(rules: Iterable[RuleImpl]) -> str:
    """Обзор раздела: правила по категориям, каждая своей таблицей."""
    ordered = _ordered(rules)
    lines = [
        INDEX_HEADER.format(
            error=_severity(Severity.ERROR),
            warning=_severity(Severity.WARNING),
            info=_severity(Severity.INFO),
        )
    ]
    for category in categories.CATEGORIES:
        section = [impl for impl in ordered if impl.category == category.name]
        if not section:
            continue
        lines.extend(
            [
                f"## {category.title}",
                "",
                "| ID | Источник | Пункты | Уровень | Название |",
                "|---|---|---|---|---|",
            ]
        )
        lines.extend(
            f"| [`{impl.id}`]({impl.id}.md) | {_origin(impl)} | {_clauses(impl)} "
            f"| {_severity(impl.severity)} | {impl.title} |"
            for impl in section
        )
        lines.append("")
    return "\n".join(lines)


def render_summary(rules: Iterable[RuleImpl]) -> str:
    """Оглавление раздела для `mkdocs-literate-nav`, по категориям правил."""
    ordered = _ordered(rules)
    lines = [f"* [Обзор]({INDEX_PAGE})"]
    for category in categories.CATEGORIES:
        section = [impl for impl in ordered if impl.category == category.name]
        if not section:
            continue
        lines.append(f"* {category.title}")
        lines.extend(f"    * [{impl.id}]({impl.id}.md)" for impl in section)
    lines.append("")
    return "\n".join(lines)


def render_rule(impl: RuleImpl, *, fixtures_root: Path | None = None) -> str:
    lines = [
        f"# {impl.id}",
        "",
        f"**{impl.title}.**",
        "",
        "| | |",
        "|---|---|",
        f"| Категория | {categories.title(impl.category)} |",
        f"| Источник требования | {_origin(impl)} |",
        f"| Пункты | {_clauses(impl)} |",
        f"| Уровень по умолчанию | {_severity(impl.severity)} |",
        f"| Объявлено в | `{impl.module}` |",
        f"| Фикстуры | `tests/fixtures/{impl.id}/` |",
        f"| Автоисправление | {'да, ключом `--fix`' if impl.fixable else 'нет'} |",
        "",
    ]
    if impl.description:
        lines.extend([impl.description, ""])
    if impl.default_off:
        lines.extend(
            [
                "!!! note",
                "",
                "    Правило выключено по умолчанию. Включается профилем:",
                "",
                "    ```toml",
                f'    enable = ["{impl.id}"]',
                "    ```",
                "",
            ]
        )
    lines.extend(_origin_note(impl))
    if impl.allow_missing_suggestion:
        lines.extend(
            [
                "!!! note",
                "",
                "    Готовое исправление правило не предлагает: оно принципиально неоднозначно.",
                "",
            ]
        )

    lines.extend(_params_section(impl))
    lines.extend(_example_section(impl, fixtures_root))
    lines.extend(_profile_section(impl))
    return "\n".join(lines)


def _origin(impl: RuleImpl) -> str:
    """Чьё требование проверяет правило: та же подпись, что и в `nk rules show`."""
    return standards.ORIGIN_LABELS[impl.origin]


def _origin_note(impl: RuleImpl) -> list[str]:
    """Примечание о происхождении там, где одних пунктов для понимания мало."""
    if impl.origin is standards.Origin.REGULATION:
        note = (
            "Ни один стандарт этого не требует: источник — положение вуза либо "
            "методические указания кафедры. Название источника и пункт объявляет "
            "[профиль](../profiles.md#стандарт-и-свой-источник-требований)."
        )
    elif impl.origin is standards.Origin.UNIVERSAL and impl.clauses:
        note = (
            "Требование нужно под любым стандартом, а пункт назван там, где оно "
            "записано: область правила пункт не сужает."
        )
    else:
        return []
    return ["!!! note", "", f"    {note}", ""]


def _clauses(impl: RuleImpl) -> str:
    """Стандарты и пункты правила: одно требование бывает записано в нескольких.

    Значение идёт в ячейку таблицы, поэтому стандарты разделены переносом строки.
    """
    if not impl.clauses:
        return NO_CLAUSE_LABEL
    return CLAUSE_SEPARATOR.join(
        f"{standards.get(key).title} п. {clause}" for key, clause in sorted(impl.clauses.items())
    )


def _severity(severity: Severity) -> str:
    """Уровень находки плашкой: стиль задаёт `docs/stylesheets/severity.css`."""
    value = severity.value
    return f'<span class="nk-severity nk-severity--{value}">{value}</span>'


def _params_section(impl: RuleImpl) -> list[str]:
    if not impl.default_params:
        return []
    lines = ["## Параметры", "", "| Параметр | По умолчанию |", "|---|---|"]
    lines.extend(
        f"| `{name}` | `{_toml(value)}` |" for name, value in sorted(impl.default_params.items())
    )
    lines.append("")
    return lines


def _toml(value: object) -> str:
    """Значение параметра так, как его пишут в профиле: `false`, а не `False`."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    return repr(value)


def _example_section(impl: RuleImpl, fixtures_root: Path | None) -> list[str]:
    example = examples.load(impl.id, fixtures_root)
    if example is None:
        return []
    return [
        "## Нарушение",
        "",
        "```latex",
        example.bad,
        "```",
        "",
        "## Как правильно",
        "",
        "```latex",
        example.good,
        "```",
        "",
    ]


def _profile_section(impl: RuleImpl) -> list[str]:
    lines = [
        "## Настройка",
        "",
        "Отключить правило либо изменить его уровень [профилем](../profiles.md):",
        "",
        "```toml",
        f'disable = ["{impl.id}"]',
        "",
        f'[rules."{impl.id}"]',
        'severity = "info"',
    ]
    if impl.default_params:
        name, value = sorted(impl.default_params.items())[0]
        lines.extend(["", f'[rules."{impl.id}".params]', f"{name} = {_toml(value)}"])
    lines.extend(["```", ""])
    return lines


def _ordered(rules: Iterable[RuleImpl]) -> list[RuleImpl]:
    """Правила по категориям в объявленном порядке, внутри категории — по имени."""
    return sorted(rules, key=lambda impl: (categories.rank(impl.category), impl.id))
