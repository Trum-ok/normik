"""Генератор docs/RULES.md."""

from collections.abc import Iterable

from nk.core.rule import RuleImpl

HEADER = """\
# Правила

Файл создаётся командой `nk rules docs` и руками не редактируется.

Идентификатор правила состоит из префикса `G732`, пункта ГОСТ 7.32-2017
и мнемонического суффикса: на один пункт стандарта может приходиться
несколько независимых проверок.
"""


def render(rules: Iterable[RuleImpl]) -> str:
    ordered = sorted(rules, key=lambda impl: (_clause_key(impl.clause), impl.id))
    lines = [
        HEADER,
        "",
        "## Сводка",
        "",
        "| ID | Пункт | Уровень | Название |",
        "|---|---|---|---|",
    ]
    for impl in ordered:
        anchor = impl.id.lower().replace(".", "")
        lines.append(
            f"| [{impl.id}](#{anchor}) | {impl.clause} | {impl.severity.value} | {impl.title} |"
        )

    lines.extend(["", "## Правила", ""])
    for impl in ordered:
        lines.append(f"### {impl.id}")
        lines.append("")
        lines.append(f"{impl.title}.")
        lines.append("")
        lines.append(f"- пункт ГОСТ 7.32-2017: {impl.clause}")
        lines.append(f"- уровень по умолчанию: `{impl.severity.value}`")
        lines.append(f"- объявлено в: `{impl.module}`")
        lines.append(f"- фикстуры: `tests/fixtures/{impl.id}/`")
        if impl.default_params:
            values = ", ".join(
                f"`{name} = {value!r}`" for name, value in sorted(impl.default_params.items())
            )
            lines.append(f"- параметры: {values}")
        if impl.allow_missing_suggestion:
            lines.append("- предложение по исправлению не формулируется: оно неоднозначно")
        lines.append("")

    return "\n".join(lines)


def _clause_key(clause: str) -> tuple[int, ...]:
    """Пункты сортируются как числа, а не как строки: 6.10 идёт после 6.9."""
    return tuple(int(part) if part.isdigit() else 0 for part in clause.split("."))
