"""Чтение исходников: комментарии, включения, позиции.

Позиции всегда указывают на исходный файл, а не на файл-агрегатор: без этого
отчёт бесполезен и человеку, и агенту.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from nk.core.diagnostics import ENCODING_FALLBACK, INPUT_CYCLE, INPUT_MISSING
from nk.core.document import Document, Line
from nk.core.finding import Finding
from nk.core.latex import VERB, literal_end
from nk.core.profile import Profile
from nk.core.suppressions import Suppressions
from nk.parse.headings import build_headings
from nk.parse.issues import ParseIssue
from nk.parse.math import build_math
from nk.parse.numbering import build_numbering
from nk.parse.structure import VERBATIM_ENVIRONMENTS, build_structure
from nk.parse.suppressions import collect

TEX_SUFFIX = ".tex"
FALLBACK_ENCODING = "cp1251"

_INPUT = re.compile(r"\\(?:input|include)\s*\{([^{}]*)\}")
_DOCUMENT = re.compile(r"\\begin\s*\{document\}")
_BEGIN = re.compile(r"\\begin\s*\{([^{}]*)\}")
_END = re.compile(r"\\end\s*\{([^{}]*)\}")


@dataclass(frozen=True, slots=True)
class ParseResult:
    document: Document
    issues: tuple[ParseIssue, ...]
    suppressions: Suppressions = field(default_factory=Suppressions)


def strip_comment(raw: str) -> str:
    """Вырезать комментарий, оставив ``\\%`` и аргумент ``\\verb`` на месте.

    Обратная косая экранирует следующий символ. Аргумент ``\\verb|...|``
    набирается буквально, и процент внутри него комментарием не является.
    """
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == "%":
            return raw[:index]
        if char != "\\":
            index += 1
            continue
        after_verb = _verb_end(raw, index)
        index = index + 2 if after_verb is None else after_verb
    return raw


def _verb_end(raw: str, start: int) -> int | None:
    """Позиция сразу за аргументом ``\\verb``, если в ``start`` стоит эта команда."""
    index = start + 1
    if not raw.startswith(VERB, index):
        return None
    index += len(VERB)
    if index < len(raw) and raw[index] == "*":
        index += 1
    return literal_end(raw, index)


def read_file(
    path: Path, overlay: Mapping[Path, str] | None = None
) -> tuple[tuple[Line, ...], tuple[ParseIssue, ...]]:
    """Прочитать один файл в строки со снятыми комментариями.

    ``overlay`` подменяет содержимое файла, не трогая диск: так ключ ``--diff``
    прогоняет несколько проходов правок, ничего не записывая.
    """
    issues: list[ParseIssue] = []
    if overlay is not None and path in overlay:
        return _to_lines(path, overlay[path]), ()

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

    return _to_lines(path, text), tuple(issues)


def _to_lines(path: Path, text: str) -> tuple[Line, ...]:
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

    return tuple(lines)


def collect_sources(paths: Iterable[Path]) -> list[Path]:
    """Развернуть аргументы командной строки в список файлов ``.tex``."""
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(path.rglob(f"*{TEX_SUFFIX}")))
        else:
            found.append(path)
    return found


def parse(
    paths: Sequence[Path],
    profile: Profile | None = None,
    overlay: Mapping[Path, str] | None = None,
) -> ParseResult:
    """Прочитать исходники, развернуть включения и собрать структуру."""
    cache: dict[Path, tuple[tuple[Line, ...], tuple[ParseIssue, ...]]] = {}
    roots = _main_first(collect_sources(paths), cache, overlay)
    base = roots[0].parent if roots else Path()

    lines: list[Line] = []
    issues: list[ParseIssue] = []
    files: list[Path] = []
    visited: set[Path] = set()

    for root in roots:
        _expand(root, base, lines, issues, files, visited, stack=(), overlay=overlay, cache=cache)

    structure, structure_issues = build_structure(lines)
    issues.extend(structure_issues)

    document = Document(
        root=Path(paths[0]) if paths else Path(),
        files=tuple(files),
        lines=tuple(lines),
        profile=profile or Profile(),
        structure=structure,
    )
    document = replace(document, headings=build_headings(document), math=build_math(document))
    document = replace(document, numbering=build_numbering(document))
    return ParseResult(
        document=document,
        issues=tuple(issues),
        suppressions=collect(document.lines),
    )


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


def _main_first(
    roots: list[Path],
    cache: dict[Path, tuple[tuple[Line, ...], tuple[ParseIssue, ...]]],
    overlay: Mapping[Path, str] | None,
) -> list[Path]:
    """Главный файл отчёта — первым, остальные в прежнем порядке.

    Порядок отчёта задают включения из главного файла. При проверке каталога обход
    иначе начинается со случайного файла, и порядок элементов определяется алфавитом
    имён — из-за чего введение оказывается «после» заключения.
    """
    return sorted(roots, key=lambda path: not _is_main(path, cache, overlay))


def _is_main(
    path: Path,
    cache: dict[Path, tuple[tuple[Line, ...], tuple[ParseIssue, ...]]],
    overlay: Mapping[Path, str] | None,
) -> bool:
    lines, _ = _cached(path, cache, overlay)
    return any(_DOCUMENT.search(line.stripped) for line in lines)


def _cached(
    path: Path,
    cache: dict[Path, tuple[tuple[Line, ...], tuple[ParseIssue, ...]]],
    overlay: Mapping[Path, str] | None,
) -> tuple[tuple[Line, ...], tuple[ParseIssue, ...]]:
    """Прочитанный файл: главный файл ищется до обхода, читать его дважды незачем."""
    if path not in cache:
        cache[path] = read_file(path, overlay)
    return cache[path]


def _expand(
    path: Path,
    base: Path,
    lines: list[Line],
    issues: list[ParseIssue],
    files: list[Path],
    visited: set[Path],
    stack: tuple[Path, ...],
    overlay: Mapping[Path, str] | None = None,
    cache: dict[Path, tuple[tuple[Line, ...], tuple[ParseIssue, ...]]] | None = None,
) -> None:
    resolved = _identity(path)
    if resolved in visited:
        return
    visited.add(resolved)

    file_lines, file_issues = _cached(path, cache if cache is not None else {}, overlay)
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
            _expand(
                target,
                base,
                lines,
                issues,
                files,
                visited,
                stack=(*stack, path),
                overlay=overlay,
                cache=cache,
            )


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
