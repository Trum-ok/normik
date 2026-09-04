"""Разбор директив подавления из комментариев.

Формы::

    \\caption{Схема установки.}   % nk: ignore
    \\caption{Схема установки.}   % nk: ignore G732-6.5.7-caption-dot
    \\caption{Схема установки.}   % nk: ignore G732-6.5.7-caption-dot -- на кафедре так принято
    % nk: ignore-file G732-6.5.1-reference-word

``ignore`` действует на строку, в которой стоит, ``ignore-file`` — на весь файл
независимо от места. Без перечня идентификаторов подавляются все находки.
"""

import re

from nk.core.document import Line
from nk.core.suppressions import Suppression, Suppressions

DIRECTIVE = re.compile(r"%\s*nk\s*:\s*(ignore-file|ignore)\b(?P<rest>[^\n]*)")
REASON_SEPARATOR = "--"
_RULE_ID = re.compile(r"[^\s,]+")


def collect(lines: tuple[Line, ...]) -> Suppressions:
    """Собрать директивы из комментариев."""
    items: list[Suppression] = []
    for line in lines:
        comment = line.raw[len(line.stripped) :]
        match = DIRECTIVE.search(comment)
        if match is None:
            continue
        rule_ids, reason = _parse_rest(match.group("rest"))
        items.append(
            Suppression(
                path=line.path,
                lineno=line.lineno,
                scope="file" if match.group(1) == "ignore-file" else "line",
                rule_ids=frozenset(rule_ids),
                reason=reason,
            )
        )
    return Suppressions(tuple(items))


def _parse_rest(rest: str) -> tuple[list[str], str]:
    head, separator, tail = rest.partition(REASON_SEPARATOR)
    reason = tail.strip() if separator else ""
    return _RULE_ID.findall(head), reason
