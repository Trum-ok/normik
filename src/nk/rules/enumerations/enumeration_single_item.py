"""Список из одного перечисления."""

from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR2105
from nk.rules._shared import LIST_ENVIRONMENTS, list_items

#: Сколько перечислений должно быть в списке.
MINIMUM = 2


@rule(
    id="enumeration-single-item",
    standards={GR2105: "6.7.1"},
    severity=Severity.ERROR,
    title="В списке перечислений меньше двух элементов",
    allow_missing_suggestion=True,
)
def enumeration_single_item(doc: Document) -> Iterable[Finding]:
    r"""Считает элементы списка, не заглядывая во вложенные списки: у вложенного
    свой счёт, и его проверяет отдельная находка на нём самом.

    ## Почему это нарушение

    Список перечислений должен содержать не менее двух перечислений. Из одного
    элемента список не образуется: перечислять нечего, и элемент оформляют
    обычным абзацем.

    ## Как исправить

    Дописать недостающие элементы либо развернуть единственный в текст абзаца.
    """
    for environment in doc.structure.find_environments(*LIST_ENVIRONMENTS):
        items = list_items(environment)
        if len(items) >= MINIMUM:
            continue
        found = "нет ни одного элемента" if not items else "один элемент"
        yield enumeration_single_item.finding(
            doc,
            environment.span,
            message=f"В списке перечислений {found}.",
            requirement="Список перечислений должен содержать не менее двух перечислений.",
        )
