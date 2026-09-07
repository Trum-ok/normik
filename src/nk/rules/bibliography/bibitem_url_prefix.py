"""Аббревиатура URL перед электронным адресом."""

from collections.abc import Iterable

from nk.core.document import Document, Line
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import rule
from nk.core.standards import GR70100
from nk.rules._bibliography import URL, entries

PREFIX = "URL:"


@rule(
    id="bibitem-url-prefix",
    standards={GR70100: "5.8.6.4"},
    severity=Severity.ERROR,
    title="Электронный адрес приведён без аббревиатуры URL",
    fixable=True,
)
def bibitem_url_prefix(doc: Document) -> Iterable[Finding]:
    r"""Проверяет, что электронному адресу в описании источника предшествует
    аббревиатура `URL:`. Адрес, набранный командой `\url`, правило видит
    наравне с набранным текстом. Записи разбираются только в списке, набранном
    в исходнике: у списка, собираемого BibTeX, описаний в `.tex` нет.

    Готовую правку правило предлагает не всегда: если перед адресом уже стоит
    другое обозначение — «Режим доступа:», как требовал прежний стандарт, —
    его нужно заменить, а не дополнить, и решает это автор.

    ## Почему это нарушение

    Электронный адрес — элемент области примечания, и опознают его по
    аббревиатуре: без неё адрес читается как часть предыдущего элемента,
    а не как сведения о доступе к ресурсу.

    ## Как исправить

    Дописать аббревиатуру перед адресом: `. — URL: http://example.ru`
    """
    for entry in entries(doc):
        for match in URL.finditer(entry.text):
            head = entry.text[: match.start()].rstrip()
            if head.endswith(PREFIX):
                continue
            line, col = entry.at(match.start())
            insertion = None if head.endswith(":") else _insertion(line, col)
            yield bibitem_url_prefix.finding(
                doc,
                line,
                message=f"Электронный адрес в описании источника {entry.key!r} приведён без «URL:».",
                requirement=(
                    "Электронный адрес ресурса в сети Интернет приводят после аббревиатуры URL."
                ),
                suggestion=f"Дописать «{PREFIX}» перед адресом.",
                col=col,
                fix=None if insertion is None else Fix(insertion, f"{PREFIX} "),
            )


def _insertion(line: Line, col: int) -> Region | None:
    """Точка вставки перед адресом либо ``None``, если адрес набран в группе.

    Внутри ``\\url{…}`` аббревиатура попала бы в аргумент команды и напечаталась
    бы частью самого адреса. Где её дописать, автор решает сам.
    """
    if col >= 2 and line.stripped[col - 2] == "{":
        return None
    return Region.at(line.path, line.lineno, col)
