"""Общие помощники правил.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила. Правилам он доступен обычным импортом.
"""

import re
from collections.abc import Iterator

from nk.core.document import Command, Document, Environment

FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*", "SCfigure", "wrapfigure"})
TABLE_ENVIRONMENTS = frozenset({"table", "table*", "longtable", "sidewaystable"})
TABULAR_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "longtable", "array"})
GRAPHIC_COMMANDS = frozenset({"includegraphics", "includesvg", "input", "includepdf"})
GRAPHIC_ENVIRONMENTS = frozenset({"tikzpicture", "pgfpicture", "picture"})

CAPTION_COMMANDS = frozenset({"caption", "caption*", "captionof"})
LABEL_COMMANDS = frozenset({"label"})
REF_COMMANDS = frozenset({"ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref", "vref"})
CITE_COMMANDS = frozenset({"cite", "citep", "citet", "citealp", "citeauthor", "nocite"})

_COMMAND = re.compile(r"\\[A-Za-z]+\*?")
_BRACES = re.compile(r"[{}$~]")


def captions(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in CAPTION_COMMANDS:
            yield command


def labels(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in LABEL_COMMANDS:
            yield command


def caption_text(command: Command) -> str:
    """Текст наименования: у ``\\captionof`` первый аргумент — тип плавающего объекта."""
    args = command.args
    if command.name == "captionof" and len(args) > 1:
        return args[1].strip()
    return args[0].strip() if args else ""


def referenced_labels(doc: Document) -> set[str]:
    """Метки, на которые в документе есть ссылка."""
    found: set[str] = set()
    for command in doc.structure.find_commands(*REF_COMMANDS):
        for arg in command.args:
            found.update(key.strip() for key in arg.split(",") if key.strip())
    return found


def cited_keys(doc: Document) -> set[str]:
    """Ключи источников, процитированные в тексте."""
    found: set[str] = set()
    for command in doc.structure.find_commands(*CITE_COMMANDS):
        for arg in command.args:
            found.update(key.strip() for key in arg.split(",") if key.strip())
    return found


def one_line(text: str) -> str:
    """Свернуть текст в одну строку: в LaTeX перевод строки внутри группы — пробел."""
    return " ".join(text.split())


def visible_text(text: str) -> str:
    """Текст без команд и служебных символов — для проверок регистра и содержания."""
    return one_line(_BRACES.sub(" ", _COMMAND.sub(" ", text)))


def first_letter(text: str) -> str:
    """Первая буква видимого текста либо пустая строка."""
    for char in visible_text(text):
        if char.isalpha():
            return char
    return ""


def has_graphic(environment: Environment) -> bool:
    return any(command.name in GRAPHIC_COMMANDS for command in environment.all_commands()) or any(
        child.name in GRAPHIC_ENVIRONMENTS for child in environment.walk()
    )


def first_graphic_line(environment: Environment) -> int | None:
    """Номер строки, с которой начинается изображение."""
    candidates = [
        command.lineno for command in environment.all_commands() if command.name in GRAPHIC_COMMANDS
    ]
    candidates.extend(
        child.span.start for child in environment.walk() if child.name in GRAPHIC_ENVIRONMENTS
    )
    return min(candidates) if candidates else None


def first_tabular_line(environment: Environment) -> int | None:
    """Номер строки, с которой начинается сама таблица."""
    starts = [
        child.span.start for child in environment.walk() if child.name in TABULAR_ENVIRONMENTS
    ]
    return min(starts) if starts else None
