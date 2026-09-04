"""Номер раздела, вписанный в заголовок вручную.

Ограничение: заголовок, начинающийся с числа вида «7.32», от ручного номера
подраздела неотличим. Такой случай правило считает номером.
"""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import heading_text, headings, one_line, structural_element

#: «1 Введение», «2.3. Методика», «4.2.1 Расчёт»
MANUAL_NUMBER = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+")

#: Многозначное число без точек — не номер раздела, а часть заголовка: год, объём, ГОСТ.
MAX_PLAIN_DIGITS = 2


@rule(
    id="G732-6.4.1-manual-section-number",
    clause="6.4.1",
    severity=Severity.ERROR,
    title="Номер раздела вписан в заголовок вручную",
)
def manual_section_number(doc: Document) -> Iterable[Finding]:
    """Ищет заголовки, начинающиеся с номера, вписанного руками: «1 Введение»,
    «2.3. Методика», «4.2.1 Расчёт».

    Ограничение: заголовок, начинающийся с числа вида «7.32», от ручного номера
    подраздела неотличим — такой случай правило считает номером. Многозначное
    число без точек — год, объём, номер стандарта — номером не считается.

    ## Почему это нарушение

    Номер рубрики формирует класс документа. Вписанный руками номер расходится
    с автоматическим при вставке или удалении раздела, и в содержании появляются
    две разные нумерации.

    ## Как исправить

    Оставить в заголовке только текст. Нумерация появится сама; ссылаться на
    раздел следует через метку.
    """
    for command in headings(doc):
        text = heading_text(command)
        if structural_element(text) is not None:
            continue
        match = MANUAL_NUMBER.match(text)
        if match is None:
            continue
        number = match.group(1)
        if "." not in number and len(number) > MAX_PLAIN_DIGITS:
            continue
        number = match.group(0).strip()
        trailing_dot = " В конце номера раздела точка не ставится." if number.endswith(".") else ""
        yield manual_section_number.finding(
            doc,
            command.span,
            message=f"Заголовок начинается с номера «{number}», вписанного вручную.",
            requirement=(
                "Порядковый номер раздела формирует класс документа; "
                "в заголовке оставляют только его текст." + trailing_dot
            ),
            suggestion=f"\\{command.name}{{{one_line(text[match.end() :])}}}",
            col=command.col,
        )
