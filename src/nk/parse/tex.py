"""Чтение исходников: комментарии, включения, позиции.

Позиции всегда указывают на исходный файл, а не на файл-агрегатор: без этого
отчёт бесполезен и человеку, и агенту.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from nk.core.document import Document, Line
from nk.core.finding import Finding
from nk.core.profile import Profile
from nk.parse.issues import ENCODING_FALLBACK, INPUT_CYCLE, INPUT_MISSING, ParseIssue
from nk.parse.structure import VERBATIM_ENVIRONMENTS, build_structure

TEX_SUFFIX = ".tex"
FALLBACK_ENCODING = "cp1251"

_INPUT = re.compile(r"\\(?:input|include)\s*\{([^{}]*)\}")
_BEGIN = re.compile(r"\\begin\s*\{([^{}]*)\}")
_END = re.compile(r"\\end\s*\{([^{}]*)\}")


@dataclass(frozen=True, slots=True)
class ParseResult:
    document: Document
    issues: tuple[ParseIssue, ...]


def strip_comment(raw: str) -> str:
    """Вырезать комментарий, оставив экранированный ``\\%`` на месте.

    Нечётное число обратных косых черт перед ``%`` означает экранирование.
    """
    for index, char in enumerate(raw):
        if char != "%":
            continue
        backslashes = 0
        probe = index - 1
        while probe >= 0 and raw[probe] == "\\":
            backslashes += 1
            probe -= 1
        if backslashes % 2 == 0:
            return raw[:index]
    return raw


def read_file(path: Path) -> tuple[tuple[Line, ...], tuple[ParseIssue, ...]]:
    """Прочитать один файл в строки со снятыми комментариями."""
    issues: list[ParseIssue] = []
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode(FALLBACK_ENCODING, errors="replace")
        issues.append(
            ParseIssue(
                code=ENCODING_FALLBACK,
                message=f"Файл не в UTF-8, прочитан как {FALLBACK_ENCODING}.",
                requirement="Исходники отчёта хранятся в UTF-8.",
                path=path,
                lineno=1,
                suggestion=f"Перекодировать файл: iconv -f {FALLBACK_ENCODING} -t utf-8",
            )
        )

    lines: list[Line] = []
    verbatim: str | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if verbatim is not None:
            stripped = raw
            end = _END.search(raw)
            if end is not None and end.group(1) == verbatim:
                verbatim = None
        else:
            stripped = strip_comment(raw)
            begin = _BEGIN.search(stripped)
            if begin is not None and begin.group(1) in VERBATIM_ENVIRONMENTS:
                verbatim = begin.group(1)
        lines.append(Line(path=path, lineno=lineno, raw=raw, stripped=stripped))

    return tuple(lines), tuple(issues)


def collect_sources(paths: Iterable[Path]) -> list[Path]:
    """Развернуть аргументы командной строки в список файлов ``.tex``."""
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(path.rglob(f"*{TEX_SUFFIX}")))
        else:
            found.append(path)
    return found


def parse(paths: Sequence[Path], profile: Profile | None = None) -> ParseResult:
    """Прочитать исходники, развернуть включения и собрать структуру."""
    roots = collect_sources(paths)
    base = roots[0].parent if roots else Path()

    lines: list[Line] = []
    issues: list[ParseIssue] = []
    files: list[Path] = []
    visited: set[Path] = set()

    for root in roots:
        _expand(root, base, lines, issues, files, visited, stack=())

    structure, structure_issues = build_structure(lines)
    issues.extend(structure_issues)

    document = Document(
        root=Path(paths[0]) if paths else Path(),
        files=tuple(files),
        lines=tuple(lines),
        profile=profile or Profile(),
        structure=structure,
    )
    return ParseResult(document=document, issues=tuple(issues))


def parse_findings(result: ParseResult) -> tuple[Finding, ...]:
    """Замечания парсера в виде находок, дополненных фрагментом и контекстом."""
    document = result.document
    return tuple(
        issue.to_finding(
            excerpt=document.excerpt(issue.path, issue.lineno),
            context=document.context(issue.path, issue.lineno),
        )
        for issue in result.issues
    )


def _expand(
    path: Path,
    base: Path,
    lines: list[Line],
    issues: list[ParseIssue],
    files: list[Path],
    visited: set[Path],
    stack: tuple[Path, ...],
) -> None:
    resolved = _identity(path)
    if resolved in visited:
        return
    visited.add(resolved)

    file_lines, file_issues = read_file(path)
    issues.extend(file_issues)
    lines.extend(file_lines)
    files.append(path)

    for line in file_lines:
        for match in _INPUT.finditer(line.stripped):
            target = _resolve(match.group(1), base, path)
            col = match.start() + 1
            if target is None:
                issues.append(_input_missing(path, line.lineno, col, match.group(1)))
                continue
            if _identity(target) in {_identity(item) for item in (*stack, path)}:
                issues.append(_input_cycle(path, line.lineno, col, target))
                continue
            _expand(target, base, lines, issues, files, visited, stack=(*stack, path))


def _resolve(argument: str, base: Path, including: Path) -> Path | None:
    name = argument.strip()
    if not name:
        return None
    for directory in (base, including.parent):
        for candidate in (directory / name, directory / f"{name}{TEX_SUFFIX}"):
            if candidate.is_file():
                return candidate
    return None


def _identity(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _input_missing(path: Path, lineno: int, col: int, argument: str) -> ParseIssue:
    return ParseIssue(
        code=INPUT_MISSING,
        message=f"Включаемый файл {argument!r} не найден.",
        requirement="Каждый \\input и \\include указывает на существующий файл исходника.",
        path=path,
        lineno=lineno,
        col=col,
        suggestion=f"Проверить путь {argument!r} относительно главного файла отчёта.",
    )


def _input_cycle(path: Path, lineno: int, col: int, target: Path) -> ParseIssue:
    return ParseIssue(
        code=INPUT_CYCLE,
        message=f"Циклическое включение файла {target.name}.",
        requirement="Включения файлов не образуют циклов.",
        path=path,
        lineno=lineno,
        col=col,
        suggestion=f"Убрать включение {target.name}: файл уже разворачивается выше по цепочке.",
    )
