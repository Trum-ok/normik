"""Генератор страниц документации по правилам.

На каждое правило — своя страница; сводка и оглавление собираются из реестра.
Файлы в `docs/rules/` создаются командой `nk rules docs` и руками не редактируются.
"""

from collections.abc import Iterable
from pathlib import Path

from nk.core.rule import RuleImpl
from nk.report import examples

INDEX_PAGE = "index.md"
SUMMARY_PAGE = "SUMMARY.md"

INDEX_HEADER = """\
# Правила

Проверяются только исходники `.tex`. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

Идентификатор правила состоит из префикса `G732`, пункта ГОСТ 7.32-2017
и мнемонического суффикса: на один пункт стандарта может приходиться
несколько независимых проверок.

Уровень `error` влияет на код возврата, `warning` и `info` — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).
"""

#: Разделы оглавления по первому числу пункта стандарта.
SECTIONS: tuple[tuple[str, str], ...] = (
    ("4", "Раздел 4. Структура отчёта"),
    ("5", "Раздел 5. Структурные элементы"),
    ("6", "Раздел 6. Правила оформления"),
)


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
    lines = [
        INDEX_HEADER,
        "| ID | Пункт | Уровень | Название |",
        "|---|---|---|---|",
    ]
    for impl in _ordered(rules):
        lines.append(
            f"| [`{impl.id}`]({impl.id}.md) | {impl.clause} "
            f"| {impl.severity.value} | {impl.title} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_summary(rules: Iterable[RuleImpl]) -> str:
    """Оглавление раздела для `mkdocs-literate-nav`."""
    ordered = _ordered(rules)
    lines = [f"* [Обзор]({INDEX_PAGE})"]
    for prefix, title in SECTIONS:
        section = [impl for impl in ordered if impl.clause.split(".")[0] == prefix]
        if not section:
            continue
        lines.append(f"* {title}")
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
        f"| Пункт ГОСТ 7.32-2017 | {impl.clause} |",
        f"| Уровень по умолчанию | `{impl.severity.value}` |",
        f"| Объявлено в | `{impl.module}` |",
        f"| Фикстуры | `tests/fixtures/{impl.id}/` |",
        f"| Автоисправление | {'да, ключом `--fix`' if impl.fixable else 'нет'} |",
        "",
    ]
    if impl.description:
        lines.extend([impl.description, ""])
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
    return sorted(rules, key=lambda impl: (_clause_key(impl.clause), impl.id))


def _clause_key(clause: str) -> tuple[int, ...]:
    """Пункты сортируются как числа, а не как строки: 6.10 идёт после 6.9."""
    return tuple(int(part) if part.isdigit() else 0 for part in clause.split("."))
