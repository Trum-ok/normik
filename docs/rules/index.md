# Правила

Проверяются только исходники `.tex`. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

Идентификатор правила состоит из префикса `G732`, пункта ГОСТ 7.32-2017
и мнемонического суффикса: на один пункт стандарта может приходиться
несколько независимых проверок.

Уровень `error` влияет на код возврата, `warning` и `info` — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).

| ID | Пункт | Уровень | Название |
|---|---|---|---|
| [`G732-4-elements-order`](G732-4-elements-order.md) | 4 | error | Структурные элементы идут не в установленном порядке |
| [`G732-4-required-element-missing`](G732-4-required-element-missing.md) | 4 | error | Отсутствует обязательный структурный элемент |
| [`G732-5.3.2-abstract-volume-info`](G732-5.3.2-abstract-volume-info.md) | 5.3.2 | error | В реферате нет сведений об объёме отчёта |
| [`G732-5.3.2.1-keywords-count`](G732-5.3.2.1-keywords-count.md) | 5.3.2.1 | error | Число ключевых слов вне допустимого диапазона |
| [`G732-5.5.2-terms-opening`](G732-5.5.2-terms-opening.md) | 5.5.2 | error | Перечень терминов не начинается с установленной фразы |
| [`G732-5.6.1-abbreviations-opening`](G732-5.6.1-abbreviations-opening.md) | 5.6.1 | error | Перечень сокращений не начинается с установленной фразы |
| [`G732-6.2.1-structural-heading-case`](G732-6.2.1-structural-heading-case.md) | 6.2.1 | error | Заголовок структурного элемента набран не прописными буквами |
| [`G732-6.2.1-structural-heading-numbered`](G732-6.2.1-structural-heading-numbered.md) | 6.2.1 | error | Заголовок структурного элемента пронумерован |
| [`G732-6.2.2-heading-empty`](G732-6.2.2-heading-empty.md) | 6.2.2 | error | Раздел или подраздел без заголовка |
| [`G732-6.2.3-heading-dot`](G732-6.2.3-heading-dot.md) | 6.2.3 | error | Заголовок заканчивается точкой |
| [`G732-6.2.4-heading-hyphenation`](G732-6.2.4-heading-hyphenation.md) | 6.2.4 | error | В заголовке задан перенос слова |
| [`G732-6.4.1-manual-section-number`](G732-6.4.1-manual-section-number.md) | 6.4.1 | error | Номер раздела вписан в заголовок вручную |
| [`G732-6.4.5-heading-depth`](G732-6.4.5-heading-depth.md) | 6.4.5 | warning | Глубина рубрикации превышает четыре уровня |
| [`G732-6.4.6-enumeration-letters`](G732-6.4.6-enumeration-letters.md) | 6.4.6 | error | В перечислении использована недопустимая буква |
| [`G732-6.5.1-figure-no-reference`](G732-6.5.1-figure-no-reference.md) | 6.5.1 | error | На рисунок нет ссылки в тексте |
| [`G732-6.5.1-reference-word`](G732-6.5.1-reference-word.md) | 6.5.1 | warning | В ссылке на иллюстрацию использовано сокращение «рис.» |
| [`G732-6.5.4-numbering-scheme-mixed`](G732-6.5.4-numbering-scheme-mixed.md) | 6.5.4 | error | Схема нумерации иллюстраций задана в документе несколько раз |
| [`G732-6.5.5-appendix-numbering`](G732-6.5.5-appendix-numbering.md) | 6.5.5 | error | Иллюстрация приложения нумеруется без его обозначения |
| [`G732-6.5.7-caption-dot`](G732-6.5.7-caption-dot.md) | 6.5.7 | error | Наименование рисунка заканчивается точкой |
| [`G732-6.5.7-caption-manual-number`](G732-6.5.7-caption-manual-number.md) | 6.5.7 | error | Номер рисунка вписан в наименование вручную |
| [`G732-6.5.7-caption-position`](G732-6.5.7-caption-position.md) | 6.5.7 | error | Наименование рисунка расположено выше изображения |
| [`G732-6.5.8-caption-capital`](G732-6.5.8-caption-capital.md) | 6.5.8 | error | Наименование рисунка начинается со строчной буквы |
| [`G732-6.5.8-caption-hyphenation`](G732-6.5.8-caption-hyphenation.md) | 6.5.8 | error | В наименовании рисунка задан перенос слова |
| [`G732-6.6.2-reference-word`](G732-6.6.2-reference-word.md) | 6.6.2 | warning | В ссылке на таблицу использовано сокращение «табл.» |
| [`G732-6.6.2-table-no-reference`](G732-6.6.2-table-no-reference.md) | 6.6.2 | error | На таблицу нет ссылки в тексте |
| [`G732-6.6.3-caption-capital`](G732-6.6.3-caption-capital.md) | 6.6.3 | error | Наименование таблицы начинается со строчной буквы |
| [`G732-6.6.3-caption-dot`](G732-6.6.3-caption-dot.md) | 6.6.3 | error | Наименование таблицы заканчивается точкой |
| [`G732-6.6.3-caption-manual-number`](G732-6.6.3-caption-manual-number.md) | 6.6.3 | error | Номер таблицы вписан в наименование вручную |
| [`G732-6.6.3-caption-position`](G732-6.6.3-caption-position.md) | 6.6.3 | error | Наименование таблицы расположено ниже самой таблицы |
| [`G732-6.6.4-appendix-numbering`](G732-6.6.4-appendix-numbering.md) | 6.6.4 | error | Таблица приложения нумеруется без его обозначения |
| [`G732-6.7.2-note-capital`](G732-6.7.2-note-capital.md) | 6.7.2 | error | Слово «Примечание» набрано со строчной буквы |
| [`G732-6.7.3-note-dash`](G732-6.7.3-note-dash.md) | 6.7.3 | error | После слова «Примечание» стоит не тире |
| [`G732-6.7.4-footnote-space`](G732-6.7.4-footnote-space.md) | 6.7.4 | error | Знак сноски отделён пробелом от поясняемого слова |
| [`G732-6.8.1-blank-line-around`](G732-6.8.1-blank-line-around.md) | 6.8.1 | error | Формула не отделена свободной строкой |
| [`G732-6.8.2-where-colon`](G732-6.8.2-where-colon.md) | 6.8.2 | error | Пояснение к формуле начинается со слова «где» с двоеточием |
| [`G732-6.8.3-formula-no-reference`](G732-6.8.3-formula-no-reference.md) | 6.8.3 | warning | Формула пронумерована, но ссылки на неё нет |
| [`G732-6.8.4-formula-reference-format`](G732-6.8.4-formula-reference-format.md) | 6.8.4 | error | Номер формулы в ссылке приведён без скобок |
| [`G732-6.8.5-appendix-numbering`](G732-6.8.5-appendix-numbering.md) | 6.8.5 | error | Формула приложения нумеруется без обозначения приложения |
| [`G732-6.9.1-cite-unresolved`](G732-6.9.1-cite-unresolved.md) | 6.9.1 | error | Ссылка указывает на отсутствующую запись списка источников |
| [`G732-6.12.1-abstract-volume-inline`](G732-6.12.1-abstract-volume-inline.md) | 6.12.1 | error | Сведения об объёме реферата приведены не в строку |
| [`G732-6.12.2-keywords-final-dot`](G732-6.12.2-keywords-final-dot.md) | 6.12.2 | error | Перечень ключевых слов заканчивается точкой |
| [`G732-6.12.2-keywords-uppercase`](G732-6.12.2-keywords-uppercase.md) | 6.12.2 | error | Ключевые слова набраны не прописными буквами |
| [`G732-6.14-terms-dash`](G732-6.14-terms-dash.md) | 6.14 | warning | В перечне терминов определение отделено дефисом |
| [`G732-6.15-abbreviations-dash`](G732-6.15-abbreviations-dash.md) | 6.15 | warning | В перечне сокращений расшифровка отделена дефисом |
| [`G732-6.16-bibitem-uncited`](G732-6.16-bibitem-uncited.md) | 6.16 | warning | На запись списка источников нет ссылок в тексте |
| [`G732-6.16-bibliography-order`](G732-6.16-bibliography-order.md) | 6.16 | error | Записи списка источников идут не в порядке появления ссылок |
| [`G732-6.16-bibtex-order-unverifiable`](G732-6.16-bibtex-order-unverifiable.md) | 6.16 | info | Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется |
| [`G732-6.17.2-appendix-no-reference`](G732-6.17.2-appendix-no-reference.md) | 6.17.2 | error | На приложение нет ссылки в тексте |
| [`G732-6.17.3-appendix-page-break`](G732-6.17.3-appendix-page-break.md) | 6.17.3 | error | Приложение не начинается с новой страницы |
| [`G732-6.17.4-appendix-letter`](G732-6.17.4-appendix-letter.md) | 6.17.4 | error | Приложение обозначено недопустимой буквой |
| [`G732-6.17.4-appendix-sequence`](G732-6.17.4-appendix-sequence.md) | 6.17.4 | error | В обозначениях приложений пропущена буква |
| [`G732-6.17.6-appendix-numbering`](G732-6.17.6-appendix-numbering.md) | 6.17.6 | error | Рубрика внутри приложения нумеруется без его обозначения |
| [`NK-STYLE-dash`](NK-STYLE-dash.md) | вне стандарта | info | Дефис вместо тире |
| [`NK-STYLE-initials-nbsp`](NK-STYLE-initials-nbsp.md) | вне стандарта | info | Инициалы не привязаны к фамилии |
| [`NK-STYLE-particle-nbsp`](NK-STYLE-particle-nbsp.md) | вне стандарта | info | Частица не привязана к предыдущему слову |
| [`NK-STYLE-preposition-nbsp`](NK-STYLE-preposition-nbsp.md) | вне стандарта | info | Предлог не привязан к следующему слову |
| [`NK-STYLE-quotes`](NK-STYLE-quotes.md) | вне стандарта | info | Прямые кавычки вместо «ёлочек» |
| [`NK-STYLE-reference-nbsp`](NK-STYLE-reference-nbsp.md) | вне стандарта | info | Номер в ссылке отделён разрывным пробелом |
| [`NK-STYLE-unit-nbsp`](NK-STYLE-unit-nbsp.md) | вне стандарта | info | Число не привязано к единице измерения |
