"""Воспроизведение счётчиков LaTeX.

Обход идёт по документу в порядке исходника: разделы двигают счётчик раздела,
``\\appendix`` и заголовки вида «ПРИЛОЖЕНИЕ А» переводят нумерацию в приложения,
плавающие окружения получают очередной номер по действующей схеме.

Ограничение: схема опознаётся по явным командам в исходниках. Если класс или
пакет кафедры задаёт её внутри ``.sty``, сюда это не попадёт и схема считается
сквозной — как в ``article`` по умолчанию.
"""

import re
from dataclasses import dataclass

from nk.core.document import Command, Document, Environment
from nk.core.headings import is_heading_call
from nk.core.numbering import EQUATION, FIGURE, TABLE, Numbered, Numbering, Scheme, SchemeChange

#: Окружения, дающие номер объекту соответствующего вида.
KINDS: dict[str, str] = {
    "figure": FIGURE,
    "figure*": FIGURE,
    "SCfigure": FIGURE,
    "table": TABLE,
    "table*": TABLE,
    "longtable": TABLE,
    "sidewaystable": TABLE,
    "equation": EQUATION,
    "align": EQUATION,
    "gather": EQUATION,
    "multline": EQUATION,
    "eqnarray": EQUATION,
    "alignat": EQUATION,
    "flalign": EQUATION,
}

SECTION_COMMANDS = frozenset({"section", "chapter"})
APPENDIX_COMMAND = "appendix"
WITHIN_COMMANDS = frozenset({"counterwithin", "counterwithin*", "numberwithin"})
RENEW_COMMAND = "renewcommand"

_APPENDIX_HEADING = re.compile(r"^\s*ПРИЛОЖЕНИЕ\s+(\S+)")
_THE_COUNTER = re.compile(r"^\\the(figure|table|equation)$")
_COMMANDS = re.compile(r"\\[A-Za-z]+\*?")


@dataclass(frozen=True, slots=True)
class _Event:
    order: tuple[int, int, int]
    command: Command | None = None
    environment: Environment | None = None


def build_numbering(doc: Document) -> Numbering:
    """Пройти документ и раздать плавающим объектам номера."""
    events = sorted(_events(doc), key=lambda event: event.order)
    letters = doc.profile.appendix_letters

    schemes: dict[str, Scheme] = dict.fromkeys((FIGURE, TABLE, EQUATION), Scheme.CONTINUOUS)
    counters: dict[str, int] = dict.fromkeys((FIGURE, TABLE, EQUATION), 0)
    section = 0
    appendix = ""
    appendix_index = 0
    # \appendix само приложения не открывает: им становится следующий \section.
    in_appendices = False

    items: list[Numbered] = []
    changes: list[SchemeChange] = []

    for event in events:
        if event.command is not None:
            command = event.command
            if command.name == APPENDIX_COMMAND:
                in_appendices = True
                appendix_index = 0
                continue

            heading = _appendix_heading(command)
            if heading is not None:
                in_appendices = True
                appendix = heading
                appendix_index = _letter_index(letters, heading, appendix_index)
                counters = _reset(counters, schemes)
                continue

            if command.name in SECTION_COMMANDS and is_heading_call(command):
                if in_appendices:
                    appendix, appendix_index = _next_appendix(letters, appendix_index)
                else:
                    section += 1
                counters = _reset(counters, schemes)
                continue

            change = _scheme_change(command)
            if change is not None:
                schemes[change.kind] = change.scheme
                changes.append(change)
            continue

        environment = event.environment
        if environment is None:
            continue
        kind = KINDS.get(environment.name)
        if kind is None or (kind is EQUATION and environment.name.endswith("*")):
            continue

        counters[kind] += 1
        items.append(
            Numbered(
                kind=kind,
                span=environment.span,
                number=_render(schemes[kind], counters[kind], section, appendix),
                scheme=schemes[kind],
                appendix=appendix,
            )
        )

    return Numbering(items=tuple(items), changes=tuple(changes))


def _events(doc: Document) -> list[_Event]:
    events = [
        _Event(order=(doc.file_index(command.path), command.lineno, command.col), command=command)
        for command in doc.structure.find_commands()
    ]
    events.extend(
        _Event(
            order=(doc.file_index(environment.path), environment.span.start, 0),
            environment=environment,
        )
        for environment in doc.structure.walk_environments()
    )
    return events


def _reset(counters: dict[str, int], schemes: dict[str, Scheme]) -> dict[str, int]:
    """Сбросить только те счётчики, которые нумеруются в пределах раздела.

    При сквозной схеме LaTeX счётчик не сбрасывает — именно поэтому рисунок
    внутри приложения получает номер из основной части.
    """
    return {
        kind: (0 if schemes[kind] is Scheme.BY_SECTION else value)
        for kind, value in counters.items()
    }


def _next_appendix(letters: str, index: int) -> tuple[str, int]:
    letter = letters[index] if index < len(letters) else letters[-1]
    return letter, index + 1


def _letter_index(letters: str, letter: str, fallback: int) -> int:
    return letters.index(letter) + 1 if letter in letters else fallback + 1


def _appendix_heading(command: Command) -> str | None:
    """Обозначение приложения, если команда — его заголовок."""
    if not command.args:
        return None
    text = _COMMANDS.sub(" ", command.args[0]).replace("{", " ").replace("}", " ").upper()
    match = _APPENDIX_HEADING.match(" ".join(text.split()))
    return match.group(1) if match is not None else None


def _scheme_change(command: Command) -> SchemeChange | None:
    """Схема нумерации, заданная ``\\counterwithin`` или переопределением ``\\thefigure``."""
    if command.name in WITHIN_COMMANDS and len(command.args) >= 2:
        kind = command.args[0].strip()
        if kind in {FIGURE, TABLE, EQUATION}:
            return SchemeChange(kind, command.path, command.lineno, command.col, Scheme.BY_SECTION)
        return None

    if command.name == RENEW_COMMAND and len(command.args) >= 2:
        match = _THE_COUNTER.match(command.args[0].strip())
        if match is None:
            return None
        scheme = (
            Scheme.BY_SECTION
            if "\\thesection" in command.args[1] or "\\thechapter" in command.args[1]
            else Scheme.CONTINUOUS
        )
        return SchemeChange(match.group(1), command.path, command.lineno, command.col, scheme)

    return None


def _render(scheme: Scheme, counter: int, section: int, appendix: str) -> str:
    if scheme is Scheme.CONTINUOUS:
        return str(counter)
    prefix = appendix if appendix else str(section)
    return f"{prefix}.{counter}"
