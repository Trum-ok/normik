"""Общее для форматов вывода."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from nk.core.document import CONTEXT_RADIUS
from nk.core.finding import MAX_EXCERPT_LENGTH, Finding, Severity, excerpt_window
from nk.core.runner import RunResult, Suppressed

#: Метки уровней в выводе для человека и для агента. Отделены от значения
#: перечисления намеренно: значение — часть контракта JSON и меняться не может,
#: а метка — вопрос представления, и однажды она может стать русской.
SEVERITY_LABELS: dict[Severity, str] = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "info",
}


#: Где опубликована документация. Адрес меняется вместе с ``site_url`` в
#: ``properdocs.yml``: код собирает ссылки сам, читать конфиг сайта он не может.
DOCS_URL = "https://trum-ok.github.io/normik/"


def rule_docs_url(rule_id: str) -> str:
    """Страница правила в документации: там же и пример нарушения."""
    return f"{DOCS_URL}rules/{rule_id}/"


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

#: Меньше этого окно не сжимают: в узком терминале лучше перенос, чем пустота.
_MIN_ROOM = 24

#: С чего начинается команда LaTeX: под ней указатель не ставят.
COMMAND_START = "\\"


def caret_line(finding: Finding, text: str) -> str | None:
    """Указатель под местом нарушения либо ``None``, если указывать нечего.

    Указатель отвечает на вопрос «какой знак не так»: пробел, дефис, кавычка,
    точка. Поэтому он не ставится под началом команды — что нарушение в этом
    ``\\bibitem`` или в этом ``\\caption``, видно и по стрелке слева, а знака,
    на который стоило бы показать, там нет.

    Указатель всегда в один знак: правило знает точку нарушения, а не его границы.
    Область автоматической правки шире — под ``\\caption{…}`` она заняла бы всю строку.

    Позиция в строке есть не у всякой находки, а фрагмент строки в выводе урезан
    по длине: указывать в пустоту хуже, чем не указывать вовсе.
    """
    return caret_at(_column(finding), text)


def _column(finding: Finding) -> int | None:
    """Позиция нарушения внутри показанного фрагмента строки."""
    return None if finding.col is None else finding.col - finding.excerpt_offset


def caret_at(col: int | None, text: str) -> str | None:
    """Указатель под колонкой показанного текста."""
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


def context_lines(finding: Finding, limit: int | None = None) -> Iterator[ContextLine]:
    """Контекст находки с указателем под местом нарушения.

    Форматы выводят его по-разному — с цветом и без, — но считается он одинаково:
    номера строк восстанавливаются из позиции находки, ширина колонки берётся
    по самому длинному номеру.

    ``limit`` — сколько знаков строки помещается в вывод. Строку нарушения
    сокращают окном вокруг самого нарушения: обрезанная по ширине терминала,
    она показала бы зачин вместо того места, о котором находка.
    """
    start = context_start(finding)
    width = len(str(start + len(finding.context) - 1))
    col = _column(finding)
    room = MAX_EXCERPT_LENGTH if limit is None else max(limit, _MIN_ROOM)
    for offset, text in enumerate(finding.context):
        lineno = start + offset
        hit = lineno == finding.lineno
        shown, shift = excerpt_window(text, col if hit else None, room)
        yield ContextLine(number=f"{lineno:>{width}}", text=shown, hit=hit)
        caret = caret_at(col - shift, shown) if hit and col is not None else None
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


def citation(finding: Finding) -> str:
    """Откуда требование: «ГОСТ 7.32-2017 п. 6.5.7».

    Идентификатор правила пункта не называет — он один на все источники, а пункт
    у каждого свой, и какой из них действует, решает профиль. Источник без
    пункта называют одним именем: у требования положения профиль объявляет
    пункт не всегда, а чьё оно — сказать всё равно нужно.
    """
    if not finding.clause:
        return finding.source
    return f"{finding.source} п. {finding.clause}" if finding.source else f"п. {finding.clause}"


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


def total_line(result: RunResult, fixed: int = 0) -> str:
    """Итог прогона, а после ``--fix`` — ещё и сколько правок применено.

    Отдельной строкой счёт правок повторял бы сам итог: в ``result`` уже
    перепроверенное состояние, то есть «осталось» — это и есть итог.
    """
    applied = f" (исправлено {fixed})" if fixed else ""
    return f"Итого: {summary_line(result.summary)}{applied}."


def fixable_line(result: RunResult) -> str | None:
    """Сколько находок снимает ключ ``--fix``.

    Без доли «N из M»: знаменатель уже стоит строкой выше, в итоге прогона.
    Команда целиком тоже не повторяется — пользователь только что её набрал,
    и от неё нужно ровно одно слово: имя ключа.
    """
    if not result.fixable:
        return None
    return f"Исправимо ключом {FIX_FLAG}: {result.fixable}"


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
