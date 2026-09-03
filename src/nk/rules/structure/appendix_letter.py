"""Буква в обозначении приложения."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import APPENDIX_LETTERS, heading_text, headings, normalize_heading

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+(\S+)")


@rule(
    id="G732-6.17.4-appendix-letter",
    clause="6.17.4",
    severity=Severity.ERROR,
    title="Приложение обозначено недопустимой буквой",
)
def appendix_letter(doc: Document) -> Iterable[Finding]:
    for command in headings(doc):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        designation = match.group(1)
        if len(designation) == 1 and designation in APPENDIX_LETTERS:
            continue
        yield appendix_letter.finding(
            doc,
            command.span,
            message=f"Приложение обозначено как «{designation}».",
            requirement=(
                "Приложения обозначают прописными буквами кириллицы начиная с А, "
                "за исключением Ё, З, Й, О, Ч, Ъ, Ы, Ь."
            ),
            suggestion=f"Использовать одну из букв: {', '.join(APPENDIX_LETTERS)}.",
            col=command.col,
        )
