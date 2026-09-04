"""Вывод для человека.

Цвет — вспомогательный канал: строка нарушения помечена «>», а не только цветом,
поэтому вывод остаётся читаемым при ``NO_COLOR=1`` и при перенаправлении в файл.
"""

from rich.console import Console
from rich.text import Text

from nk.core.finding import Finding, Severity
from nk.core.runner import RunResult
from nk.report.common import (
    SEVERITY_LABELS,
    context_lines,
    field_lines,
    finding_fields,
    fixable_line,
    group_by_file,
    summary_line,
    suppressed_line,
)

SEVERITY_STYLES: dict[Severity, str] = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}

MARKER = "> "
INDENT = "  "


def render(result: RunResult, console: Console, command: str | None = None) -> None:
    for path, findings in group_by_file(result.findings):
        console.print()
        console.print(Text(str(path), style="bold underline"))
        for finding in findings:
            _print_finding(console, finding)

    console.print()
    console.print(f"Итого: {summary_line(result.summary)}.")
    fixable = fixable_line(result, command)
    if fixable:
        console.print(Text(fixable, style="dim"))
    hidden = suppressed_line(result.suppressed)
    if hidden:
        console.print(Text(hidden, style="dim"))
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
    for label, value in finding_fields(finding):
        for text in field_lines(label, value, INDENT * 2):
            console.print(Text(text))

    for item in context_lines(finding):
        mark = MARKER if item.hit and not item.caret else "  "
        console.print(
            Text(f"{INDENT * 2}{mark}{item.number} | {item.text}"),
            style=style if item.hit else "dim",
            no_wrap=True,
            overflow="ellipsis",
        )
    console.print()
