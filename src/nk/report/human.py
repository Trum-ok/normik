"""Вывод для человека.

Цвет — вспомогательный канал: строка нарушения помечена «>», а не только цветом,
поэтому вывод остаётся читаемым при ``NO_COLOR=1`` и при перенаправлении в файл.
"""

from rich.console import Console
from rich.text import Text

from nk.core.finding import Finding, Severity
from nk.core.runner import RunResult
from nk.report.common import SEVERITY_LABELS, context_start, group_by_file, summary_line

SEVERITY_STYLES: dict[Severity, str] = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}

MARKER = "> "
INDENT = "  "


def render(result: RunResult, console: Console) -> None:
    for path, findings in group_by_file(result.findings):
        console.print()
        console.print(Text(str(path), style="bold underline"))
        for finding in findings:
            _print_finding(console, finding)

    console.print()
    console.print(f"Итого: {summary_line(result.summary)}.")
    for failed in result.failed_rules:
        console.print(
            Text(f"Правило {failed.rule_id} упало и пропущено: {failed.error}", style="yellow")
        )
    if result.findings:
        console.print(
            Text("Машинный вывод: --format json, вывод для агента: --format agent", style="dim")
        )


def _print_finding(console: Console, finding: Finding) -> None:
    style = SEVERITY_STYLES[finding.severity]
    position = f"{finding.lineno}:{finding.col}" if finding.col is not None else str(finding.lineno)

    header = Text(f"{INDENT}{position}  ")
    header.append(SEVERITY_LABELS[finding.severity], style=style)
    header.append(f"  {finding.rule_id}", style="dim")
    console.print(header)
    console.print(Text(f"{INDENT * 2}Нарушение: {finding.message}"))
    console.print(Text(f"{INDENT * 2}Требуется: {finding.requirement}"))
    if finding.suggestion:
        console.print(Text(f"{INDENT * 2}Исправить: {finding.suggestion}"))

    start = context_start(finding)
    width = len(str(start + len(finding.context) - 1))
    for offset, text in enumerate(finding.context):
        lineno = start + offset
        hit = lineno == finding.lineno
        console.print(
            Text(f"{INDENT * 2}{MARKER if hit else '  '}{lineno:>{width}} | {text}"),
            style=style if hit else "dim",
            no_wrap=True,
            overflow="ellipsis",
        )
    console.print()
