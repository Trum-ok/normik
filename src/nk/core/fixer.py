"""Применение машинных правок к исходникам.

Правки применяются по одному файлу за раз, от конца к началу: так смещения
ранних правок не сдвигают поздние. Пересекающиеся правки в один проход не
применяются — берётся первая, остальные достаются следующему проходу.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path

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
            try:
                # newline="" отключает трансляцию переводов строки: иначе правка
                # молча превратила бы CRLF-файл в LF.
                with path.open(encoding="utf-8", newline="") as handle:
                    original = handle.read()
            except (OSError, UnicodeDecodeError):
                skipped.append(path)
                continue
        text, applied = _apply(original, fixes)
        if applied:
            edits.append(FileEdit(path=path, text=text, applied=applied))

    return FixResult(edits=tuple(edits), skipped=tuple(skipped))


def write(result: FixResult) -> int:
    """Записать подготовленное содержимое на диск."""
    for edit in result.edits:
        with edit.path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(edit.text)
    return result.applied


def _apply(text: str, fixes: Sequence[Fix]) -> tuple[str, int]:
    starts = _line_starts(text)
    ordered = sorted(
        fixes,
        key=lambda fix: (fix.region.start.lineno, fix.region.start.col, fix.replacement),
    )

    accepted: list[tuple[int, int, str]] = []
    taken: list[Fix] = []
    for fix in ordered:
        start = _offset(starts, fix.region.start)
        end = _offset(starts, fix.region.end)
        if start is None or end is None or start > end:
            continue
        if any(fix.region.overlaps(other.region) for other in taken):
            continue
        taken.append(fix)
        accepted.append((start, end, fix.replacement))

    for start, end, replacement in sorted(accepted, reverse=True):
        text = text[:start] + replacement + text[end:]

    return text, len(accepted)


def _line_starts(text: str) -> list[int]:
    starts: list[int] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        starts.append(offset)
        offset += len(line)
    starts.append(offset)
    return starts


def _offset(starts: list[int], position: Position) -> int | None:
    """Смещение позиции в тексте либо ``None``, если позиция вне файла."""
    index = position.lineno - 1
    if not 0 <= index < len(starts):
        return None
    offset = starts[index] + position.col - 1
    return offset if offset <= starts[-1] else None


def diff(texts: Mapping[Path, str]) -> str:
    """Унифицированный diff между файлами на диске и подготовленным содержимым."""
    chunks: list[str] = []
    for path, text in sorted(texts.items(), key=lambda item: str(item[0])):
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                original = handle.read()
        except (OSError, UnicodeDecodeError):
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
