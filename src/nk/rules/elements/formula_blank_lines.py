"""Свободная строка выше и ниже выключной формулы."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.math import MATH_ENVIRONMENTS
from nk.core.position import Region
from nk.core.rule import rule

REQUIREMENT = "Выше и ниже каждой формулы оставляют не менее одной свободной строки."


@rule(
    id="G732-6.8.1-blank-line-around",
    clause="6.8.1",
    severity=Severity.ERROR,
    title="Формула не отделена свободной строкой",
    fixable=True,
)
def formula_blank_lines(doc: Document) -> Iterable[Finding]:
    """Проверяет строки непосредственно выше и ниже выключной формулы. Формула,
    которая целиком составляет содержимое другого окружения, отбивки не требует.

    ## Почему это нарушение

    Выше и ниже каждой формулы оставляют не менее одной свободной строки: формула
    отделяется от текста, а не втискивается в абзац.

    ## Как исправить

    Вставить пустую строку перед формулой и после неё. Пустая строка в исходнике
    разрывает абзац, поэтому пояснение со словом «где» начинают с новой строки
    сразу за формулой.
    """
    for environment in doc.structure.find_environments(*MATH_ENVIRONMENTS):
        above = doc.line_at(environment.path, environment.span.start - 1)
        below = doc.line_at(environment.path, environment.span.end + 1)

        # Формула как единственное содержимое другого окружения отбивки не требует.
        if (
            above is not None
            and not above.is_blank
            and not above.stripped.lstrip().startswith("\\begin")
        ):
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Выше формулы нет свободной строки.",
                requirement=REQUIREMENT,
                suggestion=f"Вставить пустую строку перед строкой {environment.span.start}.",
                fix=Fix(Region.at(environment.path, environment.span.start), "\n"),
            )
        if (
            below is not None
            and not below.is_blank
            and not below.stripped.lstrip().startswith("\\end")
        ):
            yield formula_blank_lines.finding(
                doc,
                environment.span,
                message="Ниже формулы нет свободной строки.",
                requirement=REQUIREMENT,
                suggestion=f"Вставить пустую строку после строки {environment.span.end}.",
                fix=Fix(Region.at(environment.path, environment.span.end + 1), "\n"),
            )
