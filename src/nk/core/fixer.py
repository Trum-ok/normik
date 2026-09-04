"""Применение машинных правок к исходникам.

Правки применяются по одному файлу за раз, от конца к началу: так смещения
ранних правок не сдвигают поздние. Пересекающиеся правки в один проход не
применяются — берётся первая, остальные достаются следующему проходу.
"""

import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from difflib import unified_diff
from errno import EACCES
from pathlib import Path
from shutil import copymode
from tempfile import NamedTemporaryFile

from nk.core.finding import Finding, Fix
from nk.core.position import Position


@dataclass(frozen=True, slots=True)
class FileEdit:
    path: Path
    text: str
    """Новое содержимое файла."""

    applied: int


@dataclass(frozen=True, slots=True)
class FixResult:
    edits: tuple[FileEdit, ...] = ()
    skipped: tuple[Path, ...] = ()
    """Файлы, которые не удалось прочитать как UTF-8."""

    @property
    def applied(self) -> int:
        return sum(edit.applied for edit in self.edits)


def plan(findings: Iterable[Finding], overlay: Mapping[Path, str] | None = None) -> FixResult:
    """Собрать новое содержимое файлов, не записывая его.

    ``overlay`` подменяет исходное содержимое: так правки накладываются
    несколькими проходами, не касаясь диска.
    """
    by_file: dict[Path, list[Fix]] = {}
    for finding in findings:
        if finding.fix is not None:
            by_file.setdefault(finding.fix.region.path, []).append(finding.fix)

    edits: list[FileEdit] = []
    skipped: list[Path] = []
    for path, fixes in sorted(by_file.items(), key=lambda item: str(item[0])):
        if overlay is not None and path in overlay:
            original = overlay[path]
        else:
            original = _read(path)
            if original is None:
                skipped.append(path)
                continue
        text, applied = _apply(original, fixes)
        if applied:
            edits.append(FileEdit(path=path, text=text, applied=applied))

    return FixResult(edits=tuple(edits), skipped=tuple(skipped))


def _read(path: Path) -> str | None:
    """Содержимое файла как есть либо ``None``, если оно не читается.

    ``newline=""`` отключает трансляцию переводов строки: иначе правка молча
    превратила бы CRLF-файл в LF.
    """
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


@dataclass(frozen=True, slots=True)
class WriteResult:
    applied: int
    failed: tuple[tuple[Path, str], ...] = ()
    """Файлы, которые записать не удалось, с причиной."""


def write(result: FixResult) -> WriteResult:
    """Записать подготовленное содержимое на диск.

    Файл, который записать не удалось, не отменяет правки остальных: причина
    возвращается вызывающему, чтобы он о ней сообщил.
    """
    applied = 0
    failed: list[tuple[Path, str]] = []
    for edit in result.edits:
        try:
            _write_atomic(edit.path, edit.text)
        except OSError as error:
            failed.append((edit.path, error.strerror or str(error)))
            continue
        applied += edit.applied
    return WriteResult(applied=applied, failed=tuple(failed))


def _write_atomic(path: Path, text: str) -> None:
    """Записать файл через временный рядом с ним.

    Открытие исходника на запись обрезало бы его до первого байта нового
    содержимого: сбой или прерывание в этот момент оставляли бы от исходника
    огрызок. Подмена готового файла атомарна.
    """
    # Символьная ссылка ведёт к реальному файлу: подмена по самой ссылке
    # заменила бы её обычным файлом.
    target = Path(os.path.realpath(path))
    # Подмена файла разрешается правами каталога, поэтому файл, закрытый от
    # записи, иначе был бы переписан молча — вопреки его правам.
    if not os.access(target, os.W_OK):
        raise PermissionError(EACCES, os.strerror(EACCES), str(target))
    handle = NamedTemporaryFile(  # noqa: SIM115 — файл закрывается ниже, до подмены
        "w",
        encoding="utf-8",
        newline="",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".nk",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text)
        copymode(target, temporary)
        os.replace(temporary, target)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _apply(text: str, fixes: Sequence[Fix]) -> tuple[str, int]:
    lines = _line_bounds(text)
    newline = _newline(text)
    ordered = sorted(
        fixes,
        key=lambda fix: (fix.region.start.lineno, fix.region.start.col, fix.replacement),
    )

    accepted: list[tuple[int, int, str]] = []
    taken: list[Fix] = []
    for fix in ordered:
        start = _offset(lines, fix.region.start)
        end = _offset(lines, fix.region.end)
        if start is None or end is None or start > end:
            continue
        if any(fix.region.overlaps(other.region) for other in taken):
            continue
        taken.append(fix)
        accepted.append((start, end, _with_newline(fix.replacement, newline)))

    for start, end, replacement in sorted(accepted, reverse=True):
        text = text[:start] + replacement + text[end:]

    return text, len(accepted)


def _newline(text: str) -> str:
    """Перевод строки файла.

    Правило пишет правку с ``\n``: знать про перевод строки конкретного файла
    ему незачем, а вставить чужой значит развести окончания строк внутри файла.
    """
    if "\r\n" in text:
        return "\r\n"
    return "\r" if "\r" in text else "\n"


def _with_newline(replacement: str, newline: str) -> str:
    if newline == "\n":
        return replacement
    return replacement.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)


def _line_bounds(text: str) -> list[tuple[int, int]]:
    """Начало каждой строки и конец её содержимого, без перевода строки.

    Последняя пара — конец файла: туда попадает вставка в строку за последней.
    """
    bounds: list[tuple[int, int]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        content = len(line.rstrip("\r\n"))
        bounds.append((offset, offset + content))
        offset += len(line)
    bounds.append((offset, offset))
    return bounds


def _offset(lines: list[tuple[int, int]], position: Position) -> int | None:
    """Смещение позиции в тексте либо ``None``, если позиции в файле нет.

    Колонка за концом строки — не позиция файла, а промах правила: смещение
    по ней ушло бы в перевод строки и дальше, в чужую строку.
    """
    index = position.lineno - 1
    if not 0 <= index < len(lines):
        return None
    start, end = lines[index]
    offset = start + position.col - 1
    return offset if start <= offset <= end else None


def diff(texts: Mapping[Path, str]) -> str:
    """Унифицированный diff между файлами на диске и подготовленным содержимым."""
    chunks: list[str] = []
    for path, text in sorted(texts.items(), key=lambda item: str(item[0])):
        original = _read(path)
        if original is None:
            continue
        chunks.extend(
            unified_diff(
                original.splitlines(keepends=True),
                text.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
    return "".join(chunks)
