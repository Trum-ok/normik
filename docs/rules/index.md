# Правила

Проверяются только исходники `.tex`. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

Правила разложены по тому, что они регулируют, а не по разделам стандарта:
у разных стандартов разделы разные, а иллюстрации остаются иллюстрациями.

Уровень `error` влияет на код возврата, `warning` и `info` — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).

## Структура отчёта

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`elements-order`](elements-order.md) | ГОСТ 7.32-2017 п. 4 | error | Структурные элементы идут не в установленном порядке |
| [`required-element-missing`](required-element-missing.md) | ГОСТ 7.32-2017 п. 4 | error | Отсутствует обязательный структурный элемент |

## Заголовки и рубрикация

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`heading-depth`](heading-depth.md) | ГОСТ 7.32-2017 п. 6.4.5 | warning | Глубина рубрикации превышает четыре уровня |
| [`heading-dot`](heading-dot.md) | ГОСТ 7.32-2017 п. 6.2.3 | error | Заголовок заканчивается точкой |
| [`heading-empty`](heading-empty.md) | ГОСТ 7.32-2017 п. 6.2.2 | error | Раздел или подраздел без заголовка |
| [`heading-hyphenation`](heading-hyphenation.md) | ГОСТ 7.32-2017 п. 6.2.4 | error | В заголовке задан перенос слова |
| [`manual-section-number`](manual-section-number.md) | ГОСТ 7.32-2017 п. 6.4.1 | error | Номер раздела вписан в заголовок вручную |
| [`section-page-break`](section-page-break.md) | ГОСТ 7.32-2017 п. 6.2.1 | error | Раздел не начинается с новой страницы |
| [`structural-heading-case`](structural-heading-case.md) | ГОСТ 7.32-2017 п. 6.2.1 | error | Заголовок структурного элемента набран не прописными буквами |
| [`structural-heading-numbered`](structural-heading-numbered.md) | ГОСТ 7.32-2017 п. 6.2.1 | error | Заголовок структурного элемента пронумерован |

## Перечисления

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`enumeration-label`](enumeration-label.md) | ГОСТ 7.32-2017 п. 6.4.6 | error | Элемент перечисления обозначен не по форме |
| [`enumeration-letters`](enumeration-letters.md) | ГОСТ 7.32-2017 п. 6.4.6 | error | В перечислении использована недопустимая буква |

## Реферат

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`abstract-text-position`](abstract-text-position.md) | ГОСТ 7.32-2017 п. 6.12.3 | error | Текст реферата начинается до перечня ключевых слов |
| [`abstract-volume-info`](abstract-volume-info.md) | ГОСТ 7.32-2017 п. 5.3.2 | error | В реферате нет сведений об объёме отчёта |
| [`abstract-volume-inline`](abstract-volume-inline.md) | ГОСТ 7.32-2017 п. 6.12.1 | error | Сведения об объёме реферата приведены не в строку |
| [`keywords-count`](keywords-count.md) | ГОСТ 7.32-2017 п. 5.3.2.1 | error | Число ключевых слов вне допустимого диапазона |
| [`keywords-final-dot`](keywords-final-dot.md) | ГОСТ 7.32-2017 п. 6.12.2 | error | Перечень ключевых слов заканчивается точкой |
| [`keywords-uppercase`](keywords-uppercase.md) | ГОСТ 7.32-2017 п. 6.12.2 | error | Ключевые слова набраны не прописными буквами |

## Термины и сокращения

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`abbreviations-dash`](abbreviations-dash.md) | ГОСТ 7.32-2017 п. 6.15 | warning | В перечне сокращений расшифровка отделена дефисом |
| [`abbreviations-opening`](abbreviations-opening.md) | ГОСТ 7.32-2017 п. 5.6.1 | error | Перечень сокращений не начинается с установленной фразы |
| [`abbreviations-order`](abbreviations-order.md) | ГОСТ 7.32-2017 п. 6.15 | error | Сокращения в перечне идут не по алфавиту |
| [`terms-dash`](terms-dash.md) | ГОСТ 7.32-2017 п. 6.14 | warning | В перечне терминов определение отделено дефисом |
| [`terms-opening`](terms-opening.md) | ГОСТ 7.32-2017 п. 5.5.2 | error | Перечень терминов не начинается с установленной фразы |
| [`terms-order`](terms-order.md) | ГОСТ 7.32-2017 п. 6.14 | error | Термины в перечне идут не по алфавиту |

## Иллюстрации

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`figure-appendix-numbering`](figure-appendix-numbering.md) | ГОСТ 7.32-2017 п. 6.5.5 | error | Иллюстрация приложения нумеруется без его обозначения |
| [`figure-caption-capital`](figure-caption-capital.md) | ГОСТ 7.32-2017 п. 6.5.8 | error | Наименование рисунка начинается со строчной буквы |
| [`figure-caption-dot`](figure-caption-dot.md) | ГОСТ 7.32-2017 п. 6.5.7 | error | Наименование рисунка заканчивается точкой |
| [`figure-caption-hyphenation`](figure-caption-hyphenation.md) | ГОСТ 7.32-2017 п. 6.5.8 | error | В наименовании рисунка задан перенос слова |
| [`figure-caption-manual-number`](figure-caption-manual-number.md) | ГОСТ 7.32-2017 п. 6.5.7 | error | Номер рисунка вписан в наименование вручную |
| [`figure-caption-position`](figure-caption-position.md) | ГОСТ 7.32-2017 п. 6.5.7 | error | Наименование рисунка расположено выше изображения |
| [`figure-no-reference`](figure-no-reference.md) | ГОСТ 7.32-2017 п. 6.5.1 | error | На рисунок нет ссылки в тексте |
| [`figure-numbering-scheme-mixed`](figure-numbering-scheme-mixed.md) | ГОСТ 7.32-2017 п. 6.5.4 | error | Схема нумерации иллюстраций задана в документе несколько раз |
| [`figure-position`](figure-position.md) | ГОСТ 7.32-2017 п. 6.5.1 | error | Иллюстрация размещена выше первой ссылки на неё |
| [`figure-reference-word`](figure-reference-word.md) | ГОСТ 7.32-2017 п. 6.5.1 | warning | В ссылке на иллюстрацию использовано сокращение «рис.» |

## Таблицы

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`table-appendix-numbering`](table-appendix-numbering.md) | ГОСТ 7.32-2017 п. 6.6.4 | error | Таблица приложения нумеруется без его обозначения |
| [`table-caption-capital`](table-caption-capital.md) | ГОСТ 7.32-2017 п. 6.6.3 | error | Наименование таблицы начинается со строчной буквы |
| [`table-caption-dot`](table-caption-dot.md) | ГОСТ 7.32-2017 п. 6.6.3 | error | Наименование таблицы заканчивается точкой |
| [`table-caption-manual-number`](table-caption-manual-number.md) | ГОСТ 7.32-2017 п. 6.6.3 | error | Номер таблицы вписан в наименование вручную |
| [`table-caption-position`](table-caption-position.md) | ГОСТ 7.32-2017 п. 6.6.3 | error | Наименование таблицы расположено ниже самой таблицы |
| [`table-diagonal`](table-diagonal.md) | ГОСТ 7.32-2017 п. 6.6.6 | error | Шапка таблицы разделена диагональной линией |
| [`table-no-reference`](table-no-reference.md) | ГОСТ 7.32-2017 п. 6.6.2 | error | На таблицу нет ссылки в тексте |
| [`table-position`](table-position.md) | ГОСТ 7.32-2017 п. 6.6.2 | error | Таблица размещена выше первой ссылки на неё |
| [`table-reference-word`](table-reference-word.md) | ГОСТ 7.32-2017 п. 6.6.2 | warning | В ссылке на таблицу использовано сокращение «табл.» |

## Формулы

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`formula-appendix-numbering`](formula-appendix-numbering.md) | ГОСТ 7.32-2017 п. 6.8.5 | error | Формула приложения нумеруется без обозначения приложения |
| [`formula-blank-line-around`](formula-blank-line-around.md) | ГОСТ 7.32-2017 п. 6.8.1 | error | Формула не отделена свободной строкой |
| [`formula-no-reference`](formula-no-reference.md) | ГОСТ 7.32-2017 п. 6.8.3 | warning | Формула пронумерована, но ссылки на неё нет |
| [`formula-reference-format`](formula-reference-format.md) | ГОСТ 7.32-2017 п. 6.8.4 | error | Номер формулы в ссылке приведён без скобок |
| [`formula-where-colon`](formula-where-colon.md) | ГОСТ 7.32-2017 п. 6.8.2 | error | Пояснение к формуле начинается со слова «где» с двоеточием |

## Примечания и сноски

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`footnote-space`](footnote-space.md) | ГОСТ 7.32-2017 п. 6.7.4 | error | Знак сноски отделён пробелом от поясняемого слова |
| [`note-capital`](note-capital.md) | ГОСТ 7.32-2017 п. 6.7.2 | error | Слово «Примечание» набрано со строчной буквы |
| [`note-dash`](note-dash.md) | ГОСТ 7.32-2017 п. 6.7.3 | error | После слова «Примечание» стоит не тире |

## Источники и ссылки на них

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`bibitem-uncited`](bibitem-uncited.md) | ГОСТ 7.32-2017 п. 6.16 | warning | На запись списка источников нет ссылок в тексте |
| [`bibliography-order`](bibliography-order.md) | ГОСТ 7.32-2017 п. 6.16 | error | Записи списка источников идут не в порядке появления ссылок |
| [`bibtex-order-unverifiable`](bibtex-order-unverifiable.md) | ГОСТ 7.32-2017 п. 6.16 | info | Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется |
| [`cite-unresolved`](cite-unresolved.md) | ГОСТ 7.32-2017 п. 6.9.1 | error | Ссылка указывает на отсутствующую запись списка источников |

## Приложения

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`appendix-internal-numbering`](appendix-internal-numbering.md) | ГОСТ 7.32-2017 п. 6.17.6 | error | Рубрика внутри приложения нумеруется без его обозначения |
| [`appendix-letter`](appendix-letter.md) | ГОСТ 7.32-2017 п. 6.17.4 | error | Приложение обозначено недопустимой буквой |
| [`appendix-no-reference`](appendix-no-reference.md) | ГОСТ 7.32-2017 п. 6.17.2 | error | На приложение нет ссылки в тексте |
| [`appendix-order`](appendix-order.md) | ГОСТ 7.32-2017 п. 6.17.2 | error | Приложения идут не в порядке ссылок на них |
| [`appendix-page-break`](appendix-page-break.md) | ГОСТ 7.32-2017 п. 6.17.3 | error | Приложение не начинается с новой страницы |
| [`appendix-sequence`](appendix-sequence.md) | ГОСТ 7.32-2017 п. 6.17.4 | error | В обозначениях приложений пропущена буква |

## Типографика

| ID | Пункты | Уровень | Название |
|---|---|---|---|
| [`initials-nbsp`](initials-nbsp.md) | вне стандартов | info | Инициалы не привязаны к фамилии |
| [`particle-nbsp`](particle-nbsp.md) | вне стандартов | info | Частица не привязана к предыдущему слову |
| [`preposition-nbsp`](preposition-nbsp.md) | вне стандартов | info | Предлог не привязан к следующему слову |
| [`reference-nbsp`](reference-nbsp.md) | вне стандартов | info | Номер в ссылке отделён разрывным пробелом |
| [`text-dash`](text-dash.md) | вне стандартов | info | Дефис вместо тире |
| [`text-quotes`](text-quotes.md) | вне стандартов | info | Прямые кавычки вместо «ёлочек» |
| [`unit-nbsp`](unit-nbsp.md) | вне стандартов | info | Число не привязано к единице измерения |
