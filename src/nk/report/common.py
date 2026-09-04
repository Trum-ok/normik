"""Общее для форматов вывода."""

from collections.abc import Iterable
from itertools import groupby
from pathlib import Path

from nk.core.document import CONTEXT_RADIUS
from nk.core.finding import Finding, Severity
from nk.core.runner import Suppressed

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


#: Чем помечают место нарушения под строкой исходника.
CARET = "^"

#: С чего начинается команда LaTeX: под ней указатель не ставят.
COMMAND_START = "\\"


def caret_line(finding: Finding, text: str) -> str | None:
    """Указатель под местом нарушения либо ``None``, если указывать нечего.

    Указатель отвечает на вопрос «какой знак не так»: пробел, дефис, кавычка,
    точка. Поэтому он не ставится под началом команды — что нарушение в этом
    ``\\bibitem`` или в этом ``\\caption``, видно и по стрелке слева, а знака,
    на который стоило бы показать, там нет.

    Указатель всегда в один знак: правило знает точку нарушения, а не его границы.
    Область машинной правки шире — под ``\\caption{…}`` она заняла бы всю строку.

    Позиция в строке есть не у всякой находки, а фрагмент строки в выводе урезан
    по длине: указывать в пустоту хуже, чем не указывать вовсе.
    """
    col = finding.col
    if col is None or col < 1 or col > len(text) + 1:
        return None
    if col <= len(text) and text[col - 1] == COMMAND_START:
        return None
    # Табуляция занимает не один знак: чтобы указатель попал под нужный символ,
    # отступ повторяет исходные пробельные знаки.
    prefix = "".join("\t" if char == "\t" else " " for char in text[: col - 1])
    return prefix + CARET


def summary_line(counts: dict[Severity, int]) -> str:
    return ", ".join(f"{counts[level]} {SEVERITY_LABELS[level]}" for level in Severity)


def field_lines(label: str, value: str, indent: str) -> list[str]:
    """Поле находки: одна строка, а многострочное значение — меткой и блоком с отступом.

    Плоский формат разбирают глазами и построчно, поэтому значение не должно
    сливаться со следующим полем.
    """
    if "\n" not in value:
        return [f"{indent}{label}: {value}"]
    return [f"{indent}{label}:", *(f"{indent}  {line.strip()}" for line in value.splitlines())]


def suppressed_line(suppressed: Suppressed) -> str | None:
    """Строка о скрытых находках либо ``None``, если ничего не скрыто."""
    if not suppressed.total:
        return None
    parts = []
    if suppressed.inline:
        parts.append(f"подавлениями в исходниках: {suppressed.inline}")
    if suppressed.baseline:
        parts.append(f"снимком: {suppressed.baseline}")
    return "Скрыто " + ", ".join(parts) + "."
