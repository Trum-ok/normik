"""Общее для форматов вывода."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from nk.core.document import CONTEXT_RADIUS
from nk.core.finding import Finding, Severity
from nk.core.runner import RunResult, Suppressed

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


@dataclass(frozen=True, slots=True)
class ContextLine:
    """Строка выводимого контекста: сам исходник либо указатель под ним."""

    number: str
    """Номер строки, выровненный по ширине; у строки с указателем — пробелы."""

    text: str
    hit: bool
    """Относится к месту нарушения: сама строка либо указатель под ней."""

    caret: bool = False
    """Это указатель, а не строка исходника."""


def context_lines(finding: Finding) -> Iterator[ContextLine]:
    """Контекст находки с указателем под местом нарушения.

    Форматы выводят его по-разному — с цветом и без, — но считается он одинаково:
    номера строк восстанавливаются из позиции находки, ширина колонки берётся
    по самому длинному номеру.
    """
    start = context_start(finding)
    width = len(str(start + len(finding.context) - 1))
    for offset, text in enumerate(finding.context):
        lineno = start + offset
        hit = lineno == finding.lineno
        yield ContextLine(number=f"{lineno:>{width}}", text=text, hit=hit)
        caret = caret_line(finding, text) if hit else None
        if caret is not None:
            yield ContextLine(number=" " * width, text=caret, hit=True, caret=True)


def finding_fields(finding: Finding) -> list[tuple[str, str]]:
    """Заполненные поля находки в порядке вывода: что не так, что требуется, что сделать."""
    pairs = (
        ("Нарушение", finding.message),
        ("Требуется", finding.requirement),
        ("Исправить", finding.suggestion or ""),
    )
    return [(label, value) for label, value in pairs if value]


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


FIX_FLAG = "--fix"
DIFF_FLAG = "--diff"


def fixable_line(result: RunResult, command: str | None = None) -> str | None:
    """Сколько находок правятся машинно и чем это сделать.

    Ключ ``--fix`` в уже отданной команде означает, что правки применены, а
    оставшееся ими не берётся: советовать тот же ключ повторно незачем.
    """
    if not result.fixable:
        return None
    counted = f"Исправимо машинно: {result.fixable} из {len(result.findings)}"
    if command is None or FIX_FLAG in command.split():
        return f"{counted}."
    return f"{counted}. Применить: {command} {FIX_FLAG}, посмотреть правки: {DIFF_FLAG}."


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
