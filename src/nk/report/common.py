"""Общее для форматов вывода."""

from collections.abc import Iterable
from itertools import groupby
from pathlib import Path

from nk.core.document import CONTEXT_RADIUS
from nk.core.finding import Finding, Severity

SEVERITY_LABELS: dict[Severity, str] = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "info",
}


def group_by_file(findings: Iterable[Finding]) -> list[tuple[Path, list[Finding]]]:
    """Находки по файлам; внутри файла — по возрастанию номера строки."""
    ordered = sorted(findings, key=lambda finding: finding.sort_key)
    return [(Path(path), list(group)) for path, group in groupby(ordered, key=lambda f: f.path)]


def context_start(finding: Finding) -> int:
    """Номер первой строки контекста.

    Контекст собирается симметрично вокруг строки нарушения и подрезается по началу
    файла, поэтому номер восстанавливается из позиции находки.
    """
    return max(1, finding.lineno - CONTEXT_RADIUS)


def summary_line(counts: dict[Severity, int]) -> str:
    return ", ".join(f"{counts[level]} {SEVERITY_LABELS[level]}" for level in Severity)
