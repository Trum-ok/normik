"""Наименование рисунка перед самим изображением."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import FIGURE_ENVIRONMENTS, captions, first_graphic_line


@rule(
    id="G732-6.5.7-caption-position",
    clause="6.5.7",
    severity=Severity.ERROR,
    title="Наименование рисунка расположено выше изображения",
)
def figure_caption_position(doc: Document) -> Iterable[Finding]:
    for environment in doc.structure.find_environments(*FIGURE_ENVIRONMENTS):
        graphic = first_graphic_line(environment)
        if graphic is None:
            continue
        for command in captions(environment):
            if command.lineno >= graphic:
                continue
            yield figure_caption_position.finding(
                doc,
                command.span,
                message="Наименование рисунка стоит выше самого изображения.",
                requirement="Слово «Рисунок», номер и наименование помещают под рисунком.",
                suggestion=f"Перенести \\{command.name} ниже строки {graphic}, после изображения.",
                col=command.col,
            )
