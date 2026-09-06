"""Буква в обозначении приложения."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import G732
from nk.rules._shared import heading_text, headings, normalize_heading

DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+(\S+)")


@rule(
    id="appendix-letter",
    standards={G732: "6.17.4"},
    severity=Severity.ERROR,
    title="Приложение обозначено недопустимой буквой",
    deprecated_ids=("G732-6.17.4-appendix-letter",),
)
def appendix_letter(doc: Document) -> Iterable[Finding]:
    """Проверяет букву в заголовке вида «ПРИЛОЖЕНИЕ А»: она должна быть одной прописной
    буквой кириллицы из допустимого набора.

    Набор допустимых обозначений задаётся [профилем](../profiles.md#обозначения-приложений):
    у другого источника требований он свой.

    ## Почему это нарушение

    Приложения обозначают буквами русского алфавита начиная с А. Ё, З, Й, О, Ч, Ъ, Ы
    и Ь пропускаются: они плохо различимы в качестве обозначения.

    ## Как исправить

    Заменить обозначение на ближайшее допустимое, сдвинув при необходимости
    обозначения следующих приложений.
    """
    letters = doc.profile.appendix_letters
    listed = ", ".join(letters)
    for command in headings(doc):
        match = DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        designation = match.group(1)
        if len(designation) == 1 and designation in letters:
            continue
        yield appendix_letter.finding(
            doc,
            command.span,
            message=f"Приложение обозначено как «{designation}».",
            requirement=(f"Приложения обозначают по порядку, допустимые обозначения: {listed}."),
            suggestion=f"Использовать одно из обозначений: {listed}.",
            col=command.col,
        )
