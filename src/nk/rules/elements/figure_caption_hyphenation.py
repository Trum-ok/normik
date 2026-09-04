"""Принудительный перенос в наименовании рисунка."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, caption_text, captions

HYPHENATION_MARKER = "\\-"


@rule(
    id="G732-6.5.8-caption-hyphenation",
    clause="6.5.8",
    severity=Severity.ERROR,
    title="В наименовании рисунка задан перенос слова",
)
def figure_caption_hyphenation(doc: Document) -> Iterable[Finding]:
    r"""Ищет в наименовании рисунка заданную вручную точку переноса `\-`.

    ## Почему это нарушение

    Перенос слов в наименовании графического материала не допускается.

    ## Как исправить

    Убрать `\-`. Длинное наименование сокращают либо переносят по границе слова.
    """
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        for command in captions(environment):
            if HYPHENATION_MARKER not in caption_text(command):
                continue
            yield figure_caption_hyphenation.finding(
                doc,
                command.span,
                message="В наименовании рисунка задана точка переноса «\\-».",
                requirement="Перенос слов в наименовании графического материала не допускается.",
                suggestion="Убрать «\\-» из наименования.",
                col=command.col,
            )
