"""Сканер окружений и команд.

Собственный сканер на стеке окружений: аргументы разбираются по балансу скобок,
позиция каждого узла сохраняется. Готовые библиотеки огрубляют позиции, а позиции
у нас в требованиях.

Ограничение, принятое сознательно: аргументы команды читаются только те, что идут
непосредственно за именем и отделены пробелами или табуляцией. Перенос группы на
следующую строку встречается редко, а жадное чтение через перевод строки
заглатывало бы следующий за командой текст.
"""

import re
from bisect import bisect_right
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from nk.core.document import Command, Environment, Line, Span, Structure
from nk.core.position import Position, Region
from nk.parse.issues import (
    ENVIRONMENT_ORPHAN_END,
    ENVIRONMENT_UNCLOSED,
    GROUP_UNCLOSED,
    ParseIssue,
)

#: Окружения, содержимое которых не разбирается: там может быть что угодно.
VERBATIM_ENVIRONMENTS = frozenset(
    {"verbatim", "Verbatim", "lstlisting", "minted", "alltt", "comment"}
)

#: Сколько групп аргументов читать за командой.
MAX_GROUPS = 4

_COMMAND_NAME = re.compile(r"[A-Za-z]+\*?")


def build_structure(lines: Sequence[Line]) -> tuple[Structure, tuple[ParseIssue, ...]]:
    """Собрать дерево окружений и команд по строкам всех файлов."""
    by_file: dict[Path, list[Line]] = {}
    for line in lines:
        by_file.setdefault(line.path, []).append(line)

    environments: list[Environment] = []
    commands: list[Command] = []
    issues: list[ParseIssue] = []
    for path, file_lines in by_file.items():
        structure, file_issues = _scan_file(path, file_lines)
        environments.extend(structure.environments)
        commands.extend(structure.commands)
        issues.extend(file_issues)

    return Structure(tuple(environments), tuple(commands)), tuple(issues)


@dataclass
class _Frame:
    name: str
    lineno: int
    col: int
    options: tuple[str, ...] = ()
    args: tuple[str, ...] = ()
    children: list[Environment] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)


class _Source:
    """Текст одного файла с отображением смещения в позицию."""

    def __init__(self, path: Path, lines: Sequence[Line]) -> None:
        self.path = path
        self.text = "\n".join(line.stripped for line in lines)
        self.last_lineno = lines[-1].lineno if lines else 1
        starts: list[int] = []
        offset = 0
        for line in lines:
            starts.append(offset)
            offset += len(line.stripped) + 1
        self._starts = starts

    def position(self, offset: int) -> tuple[int, int]:
        if not self._starts:
            return 1, 1
        index = bisect_right(self._starts, offset) - 1
        index = max(0, min(index, len(self._starts) - 1))
        return index + 1, offset - self._starts[index] + 1


def _scan_file(path: Path, lines: Sequence[Line]) -> tuple[Structure, list[ParseIssue]]:
    source = _Source(path, lines)
    text = source.text
    issues: list[ParseIssue] = []
    root = _Frame(name="", lineno=1, col=1)
    stack = [root]

    i = 0
    while i < len(text):
        if text[i] != "\\":
            i += 1
            continue

        match = _COMMAND_NAME.match(text, i + 1)
        if match is None:
            i += 2
            continue

        name = match.group(0)
        lineno, col = source.position(i)
        groups, end, unclosed = _read_groups(text, match.end())
        if unclosed:
            issues.append(_group_unclosed(path, lineno, col, name))

        if name == "begin":
            i = _open_environment(source, stack, groups, end, lineno, col, issues)
        elif name == "end":
            i = _close_environment(source, stack, groups, end, lineno, col, issues)
        else:
            end_lineno, end_col = source.position(end)
            stack[-1].commands.append(
                Command(
                    name=name,
                    path=path,
                    lineno=lineno,
                    col=col,
                    options=_of_kind(groups, "["),
                    args=_of_kind(groups, "{"),
                    span=Span(
                        path, lineno, max(lineno, end_lineno if end_col > 1 else end_lineno - 1)
                    ),
                    region=Region(path, Position(lineno, col), Position(end_lineno, end_col)),
                )
            )
            i = end

    while len(stack) > 1:
        frame = stack[-1]
        issues.append(_environment_unclosed(path, frame))
        _finish(source, stack, frame, source.last_lineno)

    return Structure(tuple(root.children), tuple(root.commands)), issues


def _open_environment(
    source: _Source,
    stack: list[_Frame],
    groups: list[tuple[str, str]],
    end: int,
    lineno: int,
    col: int,
    issues: list[ParseIssue],
) -> int:
    args = _of_kind(groups, "{")
    name = args[0] if args else ""
    if name in VERBATIM_ENVIRONMENTS:
        return _skip_verbatim(source, stack, name, end, lineno, col, issues)

    stack.append(
        _Frame(
            name=name,
            lineno=lineno,
            col=col,
            options=_of_kind(groups, "["),
            args=args[1:],
        )
    )
    return end


def _close_environment(
    source: _Source,
    stack: list[_Frame],
    groups: list[tuple[str, str]],
    end: int,
    lineno: int,
    col: int,
    issues: list[ParseIssue],
) -> int:
    args = _of_kind(groups, "{")
    name = args[0] if args else ""
    depth = _find_frame(stack, name)
    if depth is None:
        issues.append(
            ParseIssue(
                code=ENVIRONMENT_ORPHAN_END,
                message=f"\\end{{{name}}} без парного \\begin.",
                requirement="Каждое окружение открывается \\begin и закрывается \\end с тем же именем.",
                path=source.path,
                lineno=lineno,
                col=col,
                suggestion=f"Добавить \\begin{{{name}}} либо убрать лишний \\end{{{name}}}.",
            )
        )
        return end

    # Окружения, оставшиеся открытыми внутри закрываемого, восстанавливаем по месту.
    while len(stack) - 1 > depth:
        stray = stack[-1]
        issues.append(_environment_unclosed(source.path, stray))
        _finish(source, stack, stray, lineno)

    _finish(source, stack, stack[-1], lineno)
    return end


def _skip_verbatim(
    source: _Source,
    stack: list[_Frame],
    name: str,
    end: int,
    lineno: int,
    col: int,
    issues: list[ParseIssue],
) -> int:
    closing = f"\\end{{{name}}}"
    at = source.text.find(closing, end)
    if at == -1:
        issues.append(
            ParseIssue(
                code=ENVIRONMENT_UNCLOSED,
                message=f"Окружение {name} не закрыто до конца файла.",
                requirement="Каждое окружение открывается \\begin и закрывается \\end с тем же именем.",
                path=source.path,
                lineno=lineno,
                col=col,
                suggestion=f"Добавить \\end{{{name}}}.",
            )
        )
        end_lineno = source.last_lineno
        at_end = len(source.text)
    else:
        end_lineno, _ = source.position(at)
        at_end = at + len(closing)

    stack[-1].children.append(
        Environment(
            name=name,
            path=source.path,
            span=Span(source.path, lineno, end_lineno),
        )
    )
    return at_end


def _finish(source: _Source, stack: list[_Frame], frame: _Frame, end_lineno: int) -> None:
    stack.pop()
    stack[-1].children.append(
        Environment(
            name=frame.name,
            path=source.path,
            span=Span(source.path, frame.lineno, end_lineno),
            options=frame.options,
            args=frame.args,
            children=tuple(frame.children),
            commands=tuple(frame.commands),
        )
    )


def _find_frame(stack: list[_Frame], name: str) -> int | None:
    for depth in range(len(stack) - 1, 0, -1):
        if stack[depth].name == name:
            return depth
    return None


def _environment_unclosed(path: Path, frame: _Frame) -> ParseIssue:
    return ParseIssue(
        code=ENVIRONMENT_UNCLOSED,
        message=f"Окружение {frame.name} не закрыто.",
        requirement="Каждое окружение открывается \\begin и закрывается \\end с тем же именем.",
        path=path,
        lineno=frame.lineno,
        col=frame.col,
        suggestion=f"Добавить \\end{{{frame.name}}}.",
    )


def _group_unclosed(path: Path, lineno: int, col: int, name: str) -> ParseIssue:
    return ParseIssue(
        code=GROUP_UNCLOSED,
        message=f"У команды \\{name} не закрыта скобка аргумента.",
        requirement="Аргументы команды заключаются в парные скобки.",
        path=path,
        lineno=lineno,
        col=col,
        suggestion="Проверить баланс скобок в аргументе команды.",
    )


def _of_kind(groups: list[tuple[str, str]], kind: str) -> tuple[str, ...]:
    return tuple(content for open_ch, content in groups if open_ch == kind)


def _read_groups(text: str, start: int) -> tuple[list[tuple[str, str]], int, bool]:
    groups: list[tuple[str, str]] = []
    position = start
    while len(groups) < MAX_GROUPS:
        cursor = position
        while cursor < len(text) and text[cursor] in " \t":
            cursor += 1
        if cursor >= len(text) or text[cursor] not in "[{":
            break
        open_ch = text[cursor]
        content, end = _read_balanced(text, cursor, open_ch, "]" if open_ch == "[" else "}")
        if end is None:
            return groups, position, True
        groups.append((open_ch, content))
        position = end
    return groups, position, False


def _read_balanced(text: str, start: int, open_ch: str, close_ch: str) -> tuple[str, int | None]:
    depth = 0
    buffer: list[str] = []
    i = start
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            if depth > 0:
                buffer.append(text[i : i + 2])
            i += 2
            continue
        if char == open_ch:
            depth += 1
            if depth > 1:
                buffer.append(char)
        elif char == close_ch:
            depth -= 1
            if depth == 0:
                return "".join(buffer), i + 1
            buffer.append(char)
        elif depth > 0:
            buffer.append(char)
        i += 1
    return "", None
