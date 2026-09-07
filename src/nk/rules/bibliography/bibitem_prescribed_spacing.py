"""Пробелы вокруг знаков предписанной пунктуации."""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from nk.core.document import Document, Line
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import GR70100
from nk.rules._bibliography import DOI, FILLER, URL, Entry, entries, mask

#: Знаки, которые отделяются пробелом с обеих сторон. Знак «плюс» — сведения
#: о сопроводительном материале — не проверяется: в описаниях он куда чаще
#: часть заглавия, вроде «Программирование на C++».
SEPARATED = re.compile(r"(?<!/)//(?!/)|[:;/=]")

#: Знаки, после которых пробел ставят, а до — нет.
ATTACHED = re.compile(r"[.,]")

#: Сочетания, в которых косая черта — часть слова, а не знак описания.
COMPOUNDS = re.compile(r"\b(?:и/или|and/or)\b", re.IGNORECASE)


#: Слово перед двоеточием, за которым идёт значение примечания: «URL: адрес».
#: Такое двоеточие принадлежит самому примечанию, а не областям описания,
#: и пробела перед собой не требует.
LABELS = (
    "URL",
    "DOI",
    "дата обращения",
    "дата публикации",
    "дата обновления",
    "дата пересмотра",
    "режим доступа",
)


@dataclass(frozen=True, slots=True)
class Gap:
    """Недостающий или лишний пробел у предписанного знака."""

    line: Line
    col: int
    message: str
    suggestion: str
    fix: Fix | None
    """``None`` — пробел лишний, но стоит на месте перевода строки: убрать его
    значит склеить строки исходника."""


@rule(
    id="bibitem-prescribed-spacing",
    standards={GR70100: "4.6.5"},
    severity=Severity.ERROR,
    title="У знака предписанной пунктуации нет пробела",
    fixable=True,
    params={"labels": list(LABELS)},
)
def bibitem_prescribed_spacing(doc: Document) -> Iterable[Finding]:
    r"""Проверяет пробелы у знаков предписанной пунктуации в описании
    источника: `:` `;` `/` `//` `=` отделяются пробелом с обеих сторон, точка
    и запятая — только справа.

    Лишние пробелы правило не считает нарушением: в наборе они всё равно
    сходятся в один. Точку и запятую правило разбирает только там, где за ними
    сразу идёт текст: «Malashenko, B., Zemerov» и «[и др.].» набирают слитно,
    потому что рядом стоит другой знак, а не слово. Знак пропуска — многоточие
    (п. 4.6.8) — правило не трогает: у него пробелы с обеих сторон.

    Внутри сетевого адреса и идентификатора DOI знаки не разбираются, между
    цифрами тоже — там точка и двоеточие принадлежат дате, номеру или дроби.
    Двоеточие после слова из параметра `labels` — часть примечания
    («URL: адрес»), а не знак областей описания.

    Записи разбираются только в списке, набранном в исходнике: у списка,
    собираемого BibTeX, описаний в `.tex` нет.

    Знак «плюс» и скобки правило не проверяет: плюс в описаниях чаще часть
    заглавия, чем сведения о сопроводительном материале, а скобка (п. 4.6.6)
    почти всегда соседствует с грамматическим знаком, от которого предписанный
    по исходнику не отличить.

    ## Почему это нарушение

    Предписанный знак опознаёт область и элемент описания, и опознают его по
    пробелам: без них двоеточие в «Название: подзаголовок» ничем не отличается
    от двоеточия внутри заглавия. Для того знаки и отделяют пробелом в один
    печатный знак до и после — кроме точки и запятой, у которых пробел только
    после.

    ## Как исправить

    Поставить пробел: `Название: подзаголовок` → `Название : подзаголовок`,
    `Иванов И. И.,2020` → `Иванов И. И., 2020`.
    """
    params = bibitem_prescribed_spacing.params(doc)
    labels = tuple(str(item).casefold() for item in params["labels"])
    for entry in entries(doc):
        for gap in _gaps(entry, labels):
            yield bibitem_prescribed_spacing.finding(
                doc,
                gap.line,
                message=gap.message,
                requirement=(
                    "Знаки предписанной пунктуации отделяют пробелом в один печатный знак "
                    "до и после; у точки и запятой пробел оставляют только после."
                ),
                suggestion=gap.suggestion,
                col=gap.col,
                fix=gap.fix,
            )


def _gaps(entry: Entry, labels: tuple[str, ...]) -> Iterator[Gap]:
    text = mask(entry.text, URL, DOI, COMPOUNDS)
    for match in SEPARATED.finditer(text):
        sign = match.group()
        if not _spaced(text, match.start() - 1) and not _labelled(text, match.start(), labels):
            yield _missing(entry, match.start(), sign, before=True)
        if not _spaced(text, match.end()):
            yield _missing(entry, match.end(), sign, before=False)

    for match in ATTACHED.finditer(text):
        sign = match.group()
        if _numeric(text, match.start()) or _in_ellipsis(text, match.start()):
            continue
        start = _space_start(text, match.start())
        if start < match.start():
            yield _extra(entry, start, match.start(), sign)
        if not _spaced(text, match.end()) and _text_follows(text, match.end()):
            yield _missing(entry, match.end(), sign, before=False)


def _spaced(text: str, index: int) -> bool:
    """Пробел на этой позиции либо край описания: отделять там нечего."""
    return not 0 <= index < len(text) or text[index] == " "


def _numeric(text: str, index: int) -> bool:
    """Стоит ли знак между цифрами: «14.04.2018», «1,5» — это внутри элемента."""
    return text[index - 1 : index].isdigit() and text[index + 1 : index + 2].isdigit()


def _in_ellipsis(text: str, index: int) -> bool:
    """Точка в череде точек — знак пропуска.

    У многоточия пробелы с обеих сторон (п. 4.6.8), а не только справа,
    поэтому под правило о точке оно не подходит.
    """
    return "." in (text[index - 1 : index], text[index + 1 : index + 2])


def _text_follows(text: str, index: int) -> bool:
    """Идёт ли сразу за знаком слово, число или закрытый заглушкой адрес.

    Пробелом отделяют знак от текста, а не от другого знака: «Malashenko, B.,
    Zemerov», «[и др.].», «2020. – Москва» набирают слитно, и п. 4.6.11 велит
    привести в описании оба знака подряд.
    """
    char = text[index : index + 1]
    return char.isalnum() or char == FILLER


def _labelled(text: str, index: int, labels: tuple[str, ...]) -> bool:
    """Двоеточие сразу за словом примечания: «URL: адрес», «дата обращения: …»."""
    head = text[:index].casefold()
    return text[index] == ":" and head.endswith(labels)


def _space_start(text: str, index: int) -> int:
    """Начало пробелов перед знаком."""
    start = index
    while start > 0 and text[start - 1] == " ":
        start -= 1
    return start


def _missing(entry: Entry, index: int, sign: str, *, before: bool) -> Gap:
    line, col = entry.at(index)
    where = f"перед знаком «{sign}»" if before else f"после знака «{sign}»"
    return Gap(
        line=line,
        col=col,
        message=f"{where.capitalize()} нет пробела.",
        suggestion=f"Поставить пробел {where}.",
        fix=Fix(Region.at(line.path, line.lineno, col), " "),
    )


def _extra(entry: Entry, start: int, end: int, sign: str) -> Gap:
    line, col = entry.at(start)
    region = entry.region(start, end)
    return Gap(
        line=line,
        col=col,
        message=f"Перед знаком «{sign}» стоит пробел.",
        suggestion=f"Убрать пробел перед знаком «{sign}».",
        fix=None if region is None else Fix(region, ""),
    )
