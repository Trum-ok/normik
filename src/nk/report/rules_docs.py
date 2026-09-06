"""Генератор страниц документации по правилам.

На каждое правило — своя страница; сводка и оглавление собираются из реестра.
Файлы в `docs/rules/` создаются командой `nk rules docs` и руками не редактируются.
"""

from collections.abc import Iterable
from pathlib import Path

from nk.core import categories
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

Уровень `error` влияет на код возврата, `warning` и `info` — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).
"""

#: Пункт стандарта, которого у правила нет: типографика им не регулируется.
NO_CLAUSE_LABEL = "вне стандарта"


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
    lines = [INDEX_HEADER]
    for category in categories.CATEGORIES:
        section = [impl for impl in ordered if impl.category == category.name]
        if not section:
            continue
        lines.extend(
            [
                f"## {category.title}",
                "",
                "| ID | Пункт | Уровень | Название |",
                "|---|---|---|---|",
            ]
        )
        lines.extend(
            f"| [`{impl.id}`]({impl.id}.md) | {impl.clause or NO_CLAUSE_LABEL} "
            f"| {impl.severity.value} | {impl.title} |"
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
        f"| Пункт ГОСТ 7.32-2017 | {impl.clause or NO_CLAUSE_LABEL} |",
        f"| Уровень по умолчанию | `{impl.severity.value}` |",
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


def _params_section(impl: RuleImpl) -> list[str]:
    if not impl.default_params:
        return []
    lines = ["## Параметры", "", "| Параметр | По умолчанию |", "|---|---|"]
    lines.extend(
        f"| `{name}` | `{value!r}` |" for name, value in sorted(impl.default_params.items())
    )
    lines.append("")
    return lines


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
        lines.extend(["", f'[rules."{impl.id}".params]', f"{name} = {value!r}"])
    lines.extend(["```", ""])
    return lines


def _ordered(rules: Iterable[RuleImpl]) -> list[RuleImpl]:
    """Правила по категориям в объявленном порядке, внутри категории — по имени."""
    return sorted(rules, key=lambda impl: (categories.rank(impl.category), impl.id))
