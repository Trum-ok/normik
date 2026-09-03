"""Ссылка в тексте на каждое приложение."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    SECTION_DEPTH,
    heading_text,
    is_full_document,
    normalize_heading,
    ordered_commands,
)

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+([А-Я])$")
#: «в приложении А», «см. приложение~Б»
REFERENCE = re.compile(r"приложени\w*\s*~?\s*([А-Я])\b")


@rule(
    id="G732-6.17.2-appendix-no-reference",
    clause="6.17.2",
    severity=Severity.ERROR,
    title="На приложение нет ссылки в тексте",
)
def appendix_no_reference(doc: Document) -> Iterable[Finding]:
    if not is_full_document(doc):
        return

    referenced = {
        match.group(1) for line in doc.iter_lines() for match in REFERENCE.finditer(line.stripped)
    }
    for command in ordered_commands(doc, *SECTION_DEPTH):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        letter = match.group(1)
        if letter in referenced:
            continue
        yield appendix_no_reference.finding(
            doc,
            command.span,
            message=f"На приложение {letter} в тексте нет ссылки.",
            requirement=(
                "В тексте отчёта на все приложения должны быть даны ссылки; "
                "приложения располагают в порядке ссылок на них."
            ),
            suggestion=f"Добавить в текст ссылку: приведено в приложении {letter}.",
            col=command.col,
        )
