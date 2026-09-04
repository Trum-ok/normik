"""Приложение, не начатое с новой страницы."""

from collections.abc import Iterable

from nk.core.document import Command, Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.rules._shared import appendix_spans

PAGE_BREAKS = ("\\newpage", "\\clearpage", "\\cleardoublepage", "\\pagebreak")


@rule(
    id="G732-6.17.3-appendix-page-break",
    clause="6.17.3",
    severity=Severity.ERROR,
    title="Приложение не начинается с новой страницы",
    fixable=True,
)
def appendix_page_break(doc: Document) -> Iterable[Finding]:
    """Проверяет разрыв страницы перед заголовком приложения.

    ## Почему это нарушение

    Каждое приложение размещают с новой страницы. Заголовок, оформленный
    через `\\section*`, разрыва страницы сам не даёт ни в одном классе
    документа — его ставят явно.

    ## Как исправить

    Добавить `\\newpage` перед заголовком приложения.
    """
    for command, letter, _ in appendix_spans(doc):
        previous = _previous_content(doc, command)
        if previous is None or any(previous.startswith(mark) for mark in PAGE_BREAKS):
            continue
        yield appendix_page_break.finding(
            doc,
            command.span,
            message=f"Перед приложением {letter} нет разрыва страницы.",
            requirement="Каждое приложение размещают с новой страницы.",
            suggestion="\\newpage",
            col=command.col,
            fix=Fix(Region.at(command.path, command.lineno, 1), "\\newpage\n"),
        )


def _previous_content(doc: Document, command: Command) -> str | None:
    """Ближайшая непустая строка выше заголовка либо ``None``, если её нет.

    Заголовок в начале файла пропускается: разрыв мог остаться в файле,
    который его включает.
    """
    for lineno in range(command.lineno - 1, 0, -1):
        line = doc.line_at(command.path, lineno)
        if line is not None and not line.is_blank:
            return line.stripped.lstrip()
    return None
