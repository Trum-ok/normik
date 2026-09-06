"""Свободная строка выше и ниже выключной формулы."""

import re
from collections.abc import Iterable
from pathlib import Path

from nk.core.document import Document, Environment, Line
from nk.core.finding import Finding, Fix, Severity
from nk.core.math import MATH_ENVIRONMENTS
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import G732

REQUIREMENT = "Выше и ниже каждой формулы оставляют не менее одной свободной строки."
INSIDE_ARGUMENT = (
    "Вынести формулу из аргумента команды: свободная строка внутри него разрывает абзац."
)
#: Перенос строки и свободная строка: формула отделяется от соседнего текста.
BLANK_LINE = "\n\n"


@rule(
    id="formula-blank-line-around",
    standards={G732: "6.8.1"},
    severity=Severity.ERROR,
    title="Формула не отделена свободной строкой",
    fixable=True,
    deprecated_ids=("G732-6.8.1-blank-line-around",),
)
def formula_blank_lines(doc: Document) -> Iterable[Finding]:
    """Проверяет строки непосредственно выше и ниже выключной формулы. Формула,
    которая целиком составляет содержимое другого окружения, отбивки не требует.

    ## Почему это нарушение

    Выше и ниже каждой формулы оставляют не менее одной свободной строки: формула
    отделяется от текста, а не втискивается в абзац.

    ## Как исправить

    Вставить пустую строку перед формулой и после неё. Пустая строка в исходнике
    разрывает абзац, поэтому пояснение со словом «где» начинают с новой строки
    сразу за формулой.

    Формула, начатая или законченная в строке с текстом, свободной строкой не
    отделена, даже когда соседняя строка пуста: правка переносит её на
    отдельную строку вместе с отбивкой.

    Формулу внутри аргумента команды — например в сноске — правка не трогает:
    пустая строка там обрывает аргумент и валит сборку. Такую формулу выносят
    из аргумента вручную.
    """
    for environment in doc.structure.find_environments(*MATH_ENVIRONMENTS):
        above = doc.line_at(environment.path, environment.span.start - 1)
        below = doc.line_at(environment.path, environment.span.end + 1)
        inside_argument = _inside_argument(doc, environment.path, environment.span.start)

        leading = _leading(doc, environment)
        trailing = _trailing(doc, environment)

        if leading is not None:
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Формула начата в строке с текстом.",
                requirement=REQUIREMENT,
                suggestion=(
                    INSIDE_ARGUMENT
                    if inside_argument
                    else f"Перенести формулу на строку ниже строки {environment.span.start}."
                ),
                fix=None if inside_argument else Fix(leading, BLANK_LINE),
            )
        # Формула как единственное содержимое другого окружения отбивки не требует.
        elif (
            above is not None
            and not above.is_blank
            and not above.stripped.lstrip().startswith("\\begin")
        ):
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Выше формулы нет свободной строки.",
                requirement=REQUIREMENT,
                suggestion=(
                    INSIDE_ARGUMENT
                    if inside_argument
                    else f"Вставить пустую строку перед строкой {environment.span.start}."
                ),
                fix=(
                    None
                    if inside_argument
                    else Fix(Region.at(environment.path, environment.span.start), "\n")
                ),
            )
        if trailing is not None:
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Текст продолжен в строке, где формула кончается.",
                requirement=REQUIREMENT,
                suggestion=(
                    INSIDE_ARGUMENT
                    if inside_argument
                    else f"Перенести продолжение текста ниже строки {environment.span.end}."
                ),
                fix=None if inside_argument else Fix(trailing, BLANK_LINE),
            )
        elif (
            below is not None
            and not below.is_blank
            and not below.stripped.lstrip().startswith("\\end")
        ):
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Ниже формулы нет свободной строки.",
                requirement=REQUIREMENT,
                suggestion=(
                    INSIDE_ARGUMENT
                    if inside_argument
                    else f"Вставить пустую строку после строки {environment.span.end}."
                ),
                fix=(
                    None
                    if inside_argument
                    else Fix(Region.at(environment.path, environment.span.end + 1), "\n")
                ),
            )


def _inside_argument(doc: Document, path: Path, lineno: int) -> bool:
    """Открыта ли на строке фигурная группа — аргумент команды.

    Баланс скобок считается от начала абзаца: свободная строка внутри аргумента
    невозможна, поэтому выше неё группа заведомо закрыта.
    """
    lines = doc.lines_of(path)
    start = lineno - 1
    while start > 0 and not lines[start - 1].is_blank:
        start -= 1
    return sum(_balance(line.stripped) for line in lines[start : lineno - 1]) > 0


def _balance(text: str) -> int:
    """Перевес открывающих фигурных скобок над закрывающими, без экранированных."""
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        index += 1
    return depth


def _leading(doc: Document, environment: Environment) -> Region | None:
    """Промежуток между текстом слева и началом формулы, если текст там есть."""
    line = doc.line_at(environment.path, environment.span.start)
    found = _command(line, "begin", environment.name)
    if line is None or found is None:
        return None
    text = line.stripped[: found.start()]
    if not text.strip():
        return None
    return Region.in_line(line.path, line.lineno, len(text.rstrip()) + 1, found.start() + 1)


def _trailing(doc: Document, environment: Environment) -> Region | None:
    """Промежуток между концом формулы и текстом справа, если текст там есть."""
    line = doc.line_at(environment.path, environment.span.end)
    found = _command(line, "end", environment.name)
    if line is None or found is None:
        return None
    text = line.stripped[found.end() :]
    if not text.strip():
        return None
    start = found.end() + 1
    return Region.in_line(line.path, line.lineno, start, start + len(text) - len(text.lstrip()))


def _command(line: Line | None, name: str, environment: str) -> re.Match[str] | None:
    if line is None:
        return None
    return re.search(rf"\\{name}\s*\{{{re.escape(environment)}\}}", line.stripped)
