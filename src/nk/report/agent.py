"""Плоский текст для передачи в Claude Code.

Без рамок, псевдографики и ANSI: этот вывод копируется в чат. Компактный,
но самодостаточный — по нему нарушение исправляется без дополнительных пояснений.
"""

from pathlib import Path

from nk.core.finding import Finding, Severity
from nk.core.runner import RunResult
from nk.report.common import (
    SEVERITY_LABELS,
    context_start,
    field_lines,
    group_by_file,
    summary_line,
    suppressed_line,
)

#: Сколько находок показывать по умолчанию. Простыня на тысячу строк бесполезна.
DEFAULT_LIMIT = 50


def render(result: RunResult, *, command: str, limit: int = DEFAULT_LIMIT) -> str:
    shown, hidden = _limit(result.findings, limit)
    lines = [
        f"Команда: {command}",
        f"Профиль: {result.profile}, файлов проверено: {result.files_checked}",
    ]

    for path, findings in group_by_file(shown):
        for finding in findings:
            lines.append("")
            lines.extend(_render_finding(path, finding))

    lines.append("")
    lines.append(f"Итого: {summary_line(result.summary)}.")
    hidden_by_config = suppressed_line(result.suppressed)
    if hidden_by_config:
        lines.append(hidden_by_config)
    if hidden:
        lines.append(f"Скрыто находок: {hidden}. Показать все: --limit 0.")
    for failed in result.failed_rules:
        lines.append(f"Правило {failed.rule_id} упало и пропущено: {failed.error}")

    # Хвостовые пробелы — мусор в тексте, который копируют в чат.
    return "\n".join(line.rstrip() for line in lines) + "\n"


def _render_finding(path: Path, finding: Finding) -> list[str]:
    position = f"{path}:{finding.lineno}"
    if finding.col is not None:
        position = f"{position}:{finding.col}"

    lines = [f"{position}  {SEVERITY_LABELS[finding.severity]}  {finding.rule_id}"]
    lines.extend(field_lines("Нарушение", finding.message, "  "))
    lines.extend(field_lines("Требуется", finding.requirement, "  "))
    if finding.suggestion:
        lines.extend(field_lines("Исправить", finding.suggestion, "  "))
    if finding.context:
        lines.append("  Контекст:")
        start = context_start(finding)
        width = len(str(start + len(finding.context) - 1))
        for offset, text in enumerate(finding.context):
            lines.append(f"    {start + offset:>{width}} | {text}")
    return lines


def _limit(findings: tuple[Finding, ...], limit: int) -> tuple[tuple[Finding, ...], int]:
    """Урезать вывод, сохраняя все ошибки: их отбрасывать нельзя ни при каком лимите."""
    if limit <= 0 or len(findings) <= limit:
        return findings, 0

    errors = [f for f in findings if f.severity is Severity.ERROR]
    rest = [f for f in findings if f.severity is not Severity.ERROR]
    shown = [*errors, *rest[: max(0, limit - len(errors))]]
    ordered = tuple(sorted(shown, key=lambda finding: finding.sort_key))
    return ordered, len(findings) - len(ordered)
