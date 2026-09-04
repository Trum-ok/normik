"""Дефис вместо тире в тексте."""

import re
from collections.abc import Iterable
from pathlib import Path

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import section_lines, structural_headings
from nk.rules._text import is_code, prose

DASH = "—"
#: Одиночный дефис между пробелами. Последовательности «--» и «---» LaTeX сам
#: превращает в тире, их правило не трогает.
LONELY_HYPHEN = re.compile(r"(?<!-)(?<!\w)-(?!-)(?=\s)")

#: Перечни, где тире требует сам стандарт: там работают правила 6.14 и 6.15.
DEDICATED_ELEMENTS = frozenset(
    {
        "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
        "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
        "ОПРЕДЕЛЕНИЯ ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ",
    }
)


@rule(
    id="NK-STYLE-dash",
    clause="",
    severity=Severity.INFO,
    title="Дефис вместо тире",
    fixable=True,
)
def text_dash(doc: Document) -> Iterable[Finding]:
    """Находит одиночный дефис там, где по смыслу стоит тире.

    ## Почему это замечание

    ГОСТ 7.32-2017 знаков препинания не регулирует, но нормоконтроль обращает
    на это внимание: дефис и тире — разные знаки, и в наборе они выглядят
    по-разному.

    ## Как исправить

    Заменить дефис на тире. Последовательности `--` и `---` LaTeX превращает
    в тире сам, их правило не трогает. В формулах, листингах и таблицах дефис
    не проверяется: там это знак вычитания или содержимое ячейки.
    """
    dedicated = _dedicated_lines(doc)
    for line in doc.iter_lines():
        if is_code(doc, line) or (line.path, line.lineno) in dedicated:
            continue
        text = prose(doc, line)
        for match in LONELY_HYPHEN.finditer(text):
            if match.start() == 0 or text[match.start() - 1] != " ":
                continue
            yield text_dash.finding(
                doc,
                line,
                message="Между словами стоит дефис там, где нужно тире.",
                requirement="Тире и дефис — разные знаки: тире отделяет части предложения.",
                suggestion=f"Заменить дефис на тире: {DASH}",
                col=match.start() + 1,
                fix=Fix(
                    Region.in_line(line.path, line.lineno, match.start() + 1, match.end() + 1),
                    DASH,
                ),
            )


def _dedicated_lines(doc: Document) -> set[tuple[Path, int]]:
    """Строки перечней терминов и сокращений.

    Там тире требует сам стандарт, и об этом сообщают правила 6.14 и 6.15;
    общее замечание о типографике дублировало бы их на том же символе.
    """
    covered: set[tuple[Path, int]] = set()
    for command, element in structural_headings(doc):
        if element not in DEDICATED_ELEMENTS:
            continue
        covered.update((line.path, line.lineno) for line in section_lines(doc, command))
    return covered
