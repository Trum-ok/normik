"""Дата обращения к электронному ресурсу."""

import re
from collections.abc import Iterable

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import rule
from nk.core.standards import GR70100
from nk.rules._bibliography import URL, entries

#: Дата обращения по форме: фраза, число, месяц и год в круглых скобках.
ACCESS_DATE = re.compile(r"\(\s*дата\s+обращения\s*:\s*\d{2}\.\d{2}\.\d{4}\s*\)", re.IGNORECASE)

#: Дата публикации электронного журнала — её приводят вместо даты обращения.
PUBLISHED = re.compile(r"дата\s+публикации\s*:\s*\d{2}\.\d{2}\.\d{4}", re.IGNORECASE)

#: Попытка привести дату: сведения есть, но записаны не по форме.
MENTION = re.compile(r"дата\s+(?:обращения|публикации)", re.IGNORECASE)

FORM = "(дата обращения: ДД.ММ.ГГГГ)"


@rule(
    id="bibitem-url-access-date",
    standards={GR70100: "5.8.6.4"},
    severity=Severity.ERROR,
    title="У электронного адреса нет даты обращения",
)
def bibitem_url_access_date(doc: Document) -> Iterable[Finding]:
    """Проверяет, что за электронным адресом идут сведения о дате обращения:
    фраза «дата обращения», число, месяц и год в круглых скобках. Для
    электронного журнала вместо неё приводят дату публикации — такая запись
    правилом принимается. Записи разбираются только в списке, набранном
    в исходнике: у списка, собираемого BibTeX, описаний в `.tex` нет.

    ## Почему это нарушение

    Сетевой ресурс меняется и исчезает, поэтому описание указывает, каким его
    видел автор отчёта. Без даты обращения ссылка не проверяется: непонятно,
    на какое состояние страницы она указывает.

    ## Как исправить

    Дописать после адреса дату, когда ресурс открывали:
    `URL: http://example.ru (дата обращения: 04.09.2026)`
    """
    for entry in entries(doc):
        match = URL.search(entry.text)
        if match is None:
            continue
        if ACCESS_DATE.search(entry.text) or PUBLISHED.search(entry.text):
            continue
        line, col = entry.at(match.start())
        malformed = MENTION.search(entry.text) is not None
        yield bibitem_url_access_date.finding(
            doc,
            line,
            message=(
                f"Дата обращения к ресурсу {entry.key!r} записана не по форме."
                if malformed
                else f"У электронного адреса в описании {entry.key!r} нет даты обращения."
            ),
            requirement=(
                "После электронного адреса в круглых скобках указывают сведения о дате "
                "обращения к ресурсу: фразу «дата обращения», число, месяц и год."
            ),
            suggestion=f"Привести дату обращения после адреса в виде «{FORM}».",
            col=col,
        )
