"""Раздел, не начатый с новой страницы."""

from collections.abc import Iterable

from nk.core.document import Command, Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.rules._shared import (
    APPENDIX_DESIGNATION,
    SECTION_LEVEL,
    heading_level,
    heading_text,
    leading_text,
    normalize_heading,
    ordered_headings,
    page_break_fix,
    previous_content,
    starts_page,
    structural_element,
)

#: Команды, которые начинают страницу сами и разрыва перед собой не требуют.
BREAKING_COMMANDS = ("chapter",)
#: Начала, после которых рубрика и так открывает новую страницу.
PAGE_STARTS = ("\\begin{document}", "\\end{titlepage}", "\\maketitle", "\\titlepage")


@rule(
    id="G732-6.2.1-section-page-break",
    clause="6.2.1",
    severity=Severity.ERROR,
    title="Раздел не начинается с новой страницы",
    fixable=True,
    params={"breaking_commands": list(BREAKING_COMMANDS), "structural_only": False},
)
def section_page_break(doc: Document) -> Iterable[Finding]:
    r"""Проверяет разрыв страницы перед рубрикой уровня раздела — и структурного
    элемента, и раздела основной части. Приложения проверяет отдельное правило
    п. 6.17.3. Рубрика в начале файла пропускается: разрыв мог остаться в файле,
    который её включает.

    Рубрика, которая открывает страницу сама, разрыва не требует: `\chapter`,
    а также макрос шаблона, если `\newpage` вписан внутрь его определения.
    Макрос, объявленный в `.sty`, парсеру не виден — такие команды перечисляют
    параметром `breaking_commands`.

    Параметр `structural_only` сужает правило до структурных элементов: разделы
    основной части с новой страницы требует не всякий источник требований.

    ## Почему это нарушение

    Каждый структурный элемент и каждый раздел основной части начинают
    с новой страницы: раздел, начатый посреди листа, читается как продолжение
    предыдущего.

    ## Как исправить

    Добавить `\newpage` перед заголовком раздела.
    """
    params = section_page_break.params(doc)
    breaking = tuple(params["breaking_commands"])
    structural_only = bool(params["structural_only"])
    requirement = (
        "Каждый структурный элемент начинают с новой страницы."
        if structural_only
        else "Каждый структурный элемент и каждый раздел основной части начинают с новой страницы."
    )
    for command in ordered_headings(doc):
        if heading_level(doc, command) != SECTION_LEVEL:
            continue
        if structural_only and structural_element(doc, heading_text(command)) is None:
            continue
        if doc.headings.breaks_page(command.name) or _breaks_itself(command, breaking):
            continue
        if APPENDIX_DESIGNATION.match(normalize_heading(heading_text(command))):
            continue
        leading = leading_text(doc, command)
        previous = previous_content(doc, command)
        if starts_page(leading) if leading else _opens_page(previous):
            continue
        yield section_page_break.finding(
            doc,
            command.span,
            message="Перед заголовком раздела нет разрыва страницы.",
            requirement=requirement,
            suggestion="\\newpage",
            col=command.col,
            fix=page_break_fix(doc, command),
        )


def _opens_page(previous: str | None) -> bool:
    """Открыта ли новая страница тем, что стоит выше рубрики."""
    return previous is None or starts_page(previous) or previous.startswith(PAGE_STARTS)


def _breaks_itself(command: Command, breaking: tuple[str, ...]) -> bool:
    """Открывает ли команда рубрикации новую страницу сама, без ``\\newpage``."""
    return command.name.rstrip("*") in breaking
