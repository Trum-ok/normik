"""Разбор команд рубрикации документа.

Шаблоны кафедр почти всегда прячут заголовок за собственным макросом:
``\\newcommand{\\ssr}[1]{\\section*{\\centering #1}}``, а дальше в тексте стоит
``\\ssr{ВВЕДЕНИЕ}``. Без разбора определений такой заголовок для правил рубрикации
не существует, и отчёт получает ошибки об отсутствии введения и заключения.

Ограничения, принятые сознательно:

* макрос считается заголовком, только если текст заголовка приходит к нему
  параметром (``#1``); макрос с намертво вписанным названием не опознаётся,
  потому что подставить его текст в находку всё равно нечем;
* определения читаются из исходников отчёта. Макрос, объявленный в ``.sty``
  или через ``\\@startsection``, сюда не попадёт.
"""

import re

from nk.core.document import Document
from nk.core.headings import CHAPTER, Heading, Headings, base_headings

#: Формы объявления макроса: ``\newcommand{\ssr}``, ``\def\ssr``.
_DEFINITION = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|def)\*?\s*"
    r"(?:\{\s*\\([A-Za-z@]+)\s*\}|\\([A-Za-z@]+))"
)

#: Команда внутри тела макроса.
_COMMAND = re.compile(r"\\([A-Za-z@]+\*?)")

#: Объявление параметров перед телом: ``[1][по умолчанию]``, ``#1#2``.
_PARAMETERS = re.compile(r"(?:\s|#\d|\[[^\[\]]*\])*")

_PARAMETER = "#"
MAX_ALIAS_PASSES = 4
"""Сколько раз разрешать макросы через макросы: цепочки глубже в шаблонах не встречаются."""


def build_headings(doc: Document) -> Headings:
    """Собрать карту команд рубрикации: собственные команды LaTeX и макросы шаблона."""
    definitions = dict(_definitions(doc))
    aliases = _resolve(definitions)

    shifted = _has_chapters(doc, aliases)
    commands = base_headings(shifted)
    for name, target in aliases.items():
        if name in commands:
            continue
        base = commands[target]
        commands[name] = Heading(
            name=name, depth=base.depth, numbered=base.numbered, alias_of=target
        )
    return Headings(commands)


def _definitions(doc: Document) -> list[tuple[str, str]]:
    """Пары «имя макроса — тело» по всем файлам отчёта."""
    found: list[tuple[str, str]] = []
    for path in doc.files:
        text = "\n".join(line.stripped for line in doc.lines_of(path))
        for match in _DEFINITION.finditer(text):
            name = match.group(1) or match.group(2)
            parameters = _PARAMETERS.match(text, match.end())
            body = _body(text, parameters.end() if parameters else match.end())
            if name and body:
                found.append((name, body))
    return found


def _body(text: str, start: int) -> str:
    """Группа в фигурных скобках с учётом вложенности и экранирования."""
    if start >= len(text) or text[start] != "{":
        return ""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index]
        index += 1
    return ""


def _resolve(definitions: dict[str, str]) -> dict[str, str]:
    """Макросы, сводящиеся к команде рубрикации, с указанием этой команды."""
    known = dict(base_headings())
    aliases: dict[str, str] = {}
    for _ in range(MAX_ALIAS_PASSES):
        grew = False
        for name, body in definitions.items():
            if name in aliases or name in known:
                continue
            target = _target(body, known, aliases)
            if target is None:
                continue
            aliases[name] = target
            grew = True
        if not grew:
            break
    return aliases


def _target(body: str, known: dict[str, Heading], aliases: dict[str, str]) -> str | None:
    """Команда рубрикации, которой макрос передаёт свой параметр.

    Параметр обязателен: макрос, который печатает заголовок с собственным текстом,
    а аргумент расходует на что-то другое, заголовком шаблона не является.
    """
    for match in _COMMAND.finditer(body):
        name = match.group(1)
        target = name if name in known else aliases.get(name)
        if target is None:
            continue
        parameters = _PARAMETERS.match(body, match.end())
        argument = _body(body, parameters.end() if parameters else match.end())
        if _PARAMETER in argument:
            return target
    return None


def _has_chapters(doc: Document, aliases: dict[str, str]) -> bool:
    """Разбит ли отчёт на главы: тогда ``\\section`` в нём подраздел."""
    chapters = {name for name in aliases if aliases[name].startswith(CHAPTER)}
    chapters.update(name for name in base_headings() if name.startswith(CHAPTER))
    return any(doc.structure.find_commands(*chapters))
