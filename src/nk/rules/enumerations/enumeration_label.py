"""Форма обозначения элемента перечисления."""

from collections.abc import Iterable

from nk.core.document import Command, Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732, GR2105
from nk.rules._shared import DASH, ITEM_COMMAND, parse_enumeration_label

#: Знаки, которыми записывают маркер перечисления. Какой из них верен, задаёт
#: профиль: ГОСТ 7.32 требует тире, ГОСТ Р 2.105 — дефиса.
MARKERS = ("-", "--", "---", "–", "—", "*", "•", "·")

#: Алфавиты, буквами которых обозначают элементы перечисления.
CYRILLIC = "cyrillic"
LATIN = "latin"


@rule(
    id="enumeration-label",
    standards={G732: "6.4.6", GR2105: "6.7.4"},
    severity=Severity.ERROR,
    title="Элемент перечисления обозначен не по форме",
    fixable=True,
    params={"marker": DASH, "alphabets": [CYRILLIC]},
    deprecated_ids=("G732-6.4.6-enumeration-label",),
)
def enumeration_label(doc: Document) -> Iterable[Finding]:
    r"""Проверяет форму обозначения, заданного явно — `\item[а)]` и подобных:
    маркер, алфавит буквы, её регистр и знак после обозначения. Перечисление
    без явных обозначений набирает маркеры средствами класса документа, и по
    исходникам о них судить нельзя. Какая именно буква допустима, проверяет
    отдельное правило того же пункта.

    ## Почему это нарушение

    Перед каждым элементом перечисления ставят тире. Если на элементы нужно
    ссылаться, вместо тире печатают строчную букву русского алфавита или
    арабскую цифру, после которых ставят скобку: точка после обозначения
    делает элемент похожим на пункт рубрикации.

    ## Как исправить

    Привести обозначение к принятой форме: `\item[--]` заменить на маркер,
    принятый источником требований, `\item[1.]` — на `\item[1)]`.

    Маркер и допустимые алфавиты задаются параметрами: ГОСТ 7.32 требует тире
    и русских букв, ГОСТ Р 2.105 — дефиса и русских либо латинских.
    """
    params = enumeration_label.params(doc)
    marker = str(params["marker"])
    alphabets = frozenset(str(item) for item in params["alphabets"])
    for command in doc.structure.find_commands(ITEM_COMMAND):
        for option in command.options:
            finding = _check(doc, command, option, marker, alphabets)
            if finding is not None:
                yield finding


def _check(
    doc: Document, command: Command, option: str, marker: str, alphabets: frozenset[str]
) -> Finding | None:
    label = option.strip()
    if not label:
        return None
    if label == marker:
        return None
    if label in MARKERS:
        return _finding(
            doc, command, marker, f"Элемент перечисления помечен «{label}», а не «{marker}»."
        )

    parsed = parse_enumeration_label(label)
    if parsed is None:
        return None
    mark, tail = parsed
    if mark.isascii() and mark.isalpha() and LATIN not in alphabets:
        return _finding(
            doc,
            command,
            None,
            f"Элемент перечисления обозначен латинской буквой «{mark}».",
        )
    if mark.isalpha() and mark != mark.lower():
        return _finding(
            doc,
            command,
            f"{mark.lower()})",
            f"Элемент перечисления обозначен прописной буквой «{mark}».",
        )
    if tail != ")":
        found = "точкой" if tail == "." else "ничем"
        return _finding(
            doc,
            command,
            f"{mark})",
            f"Обозначение «{mark}» отделено от текста {found}, а не скобкой.",
        )
    return None


REQUIREMENT = (
    "Элементы перечисления обозначают маркером либо строчной буквой или арабской цифрой со скобкой."
)


def _finding(doc: Document, command: Command, label: str | None, message: str) -> Finding:
    """Находка с правкой, если замена однозначна.

    Для латинской буквы замены нет: какая русская буква встанет на её место,
    зависит от порядкового номера элемента в перечислении.
    """
    if label is None:
        return enumeration_label.finding(
            doc,
            command.span,
            message=message,
            requirement=REQUIREMENT,
            suggestion="Заменить букву на строчную букву русского алфавита со скобкой.",
            col=command.col,
        )
    return enumeration_label.finding(
        doc,
        command.span,
        message=message,
        requirement=REQUIREMENT,
        suggestion=f"\\item[{label}]",
        col=command.col,
        fix=command.region,
    )
