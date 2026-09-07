"""Знак между областями библиографического описания."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.rule import rule
from nk.core.standards import GR70100
from nk.rules._bibliography import DOI, EN_DASH, URL, Entry, entries, mask

#: Точка и следом тире в любом написании: сколько-то дефисов подряд либо готовый
#: знак. Пробелы вокруг тире входят в совпадение — их наличие и проверяется.
#: Хвостовой пробел берётся один: лишние на набор не влияют, а править перенос
#: строки, оказавшийся на их месте, правило не станет.
SEPARATOR = re.compile(r"\. *(?:-{1,3}|[–—]) ?")

#: Написания, которые в наборе дают «точку и тире» как её рисует стандарт:
#: короткое тире знаком либо лигатурой ``--``.
CORRECT = (f". {EN_DASH} ", ". -- ")

REPLACEMENT = f". {EN_DASH} "


@rule(
    id="bibitem-area-separator",
    standards={GR70100: "4.6.2"},
    severity=Severity.ERROR,
    title="Области описания разделены не знаком «точка и тире»",
    fixable=True,
)
def bibitem_area_separator(doc: Document) -> Iterable[Finding]:
    r"""Проверяет знак между областями описания: точка, короткое тире и по
    одному пробелу вокруг тире. Короткое тире набирают знаком «–» либо
    лигатурой `--`; длинное тире `---`, дефис и слипшиеся написания вроде
    `.-` — нарушение.

    Внутри сетевого адреса и идентификатора DOI знаки не разбираются: там они
    принадлежат самому адресу. Записи разбираются только в списке, набранном
    в исходнике: у списка, собираемого BibTeX, описаний в `.tex` нет.

    ## Почему это нарушение

    Каждой области описания, кроме первой, предшествует предписанный знак
    «точка и тире». По нему в наборе опознают границу области, поэтому знак
    один и тот же во всех описаниях — и по начертанию, и по пробелам.

    ## Как исправить

    Привести знак к виду `. -- ` либо `. – `: `2020.--- 250 с.` →
    `2020. -- 250 с.`
    """
    for entry in entries(doc):
        text = mask(entry.text, URL, DOI)
        for match in SEPARATOR.finditer(text):
            if match.group() in CORRECT:
                continue
            line, col = entry.at(match.start())
            yield bibitem_area_separator.finding(
                doc,
                line,
                message=(
                    f"Области описания источника {entry.key!r} разделены "
                    f"«{match.group().strip()}», а не знаком «точка и тире»."
                ),
                requirement=(
                    "Каждой области описания, кроме первой, предшествует предписанный "
                    "знак «точка и тире» с пробелами вокруг тире."
                ),
                suggestion=(
                    f"Разделить области знаком «{REPLACEMENT.strip()}»: "
                    "точка, пробел, короткое тире, пробел."
                ),
                col=col,
                fix=_fix(entry, match),
            )


def _fix(entry: Entry, match: re.Match[str]) -> Fix | None:
    """Правка знака, если он умещается в строку исходника.

    Знак, у которого пробел справа — это перевод строки, правится без него:
    пробел за тире даёт сам перенос, а строки склеивать не приходится.
    """
    for end, replacement in ((match.end(), REPLACEMENT), (match.end() - 1, REPLACEMENT.rstrip())):
        region = entry.region(match.start(), end)
        if region is not None:
            return Fix(region, replacement)
    return None
