# Правила

Проверяются только исходники `.tex`. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

Правила разложены по тому, что они регулируют, а не по разделам стандарта:
у разных стандартов разделы разные, а иллюстрации остаются иллюстрациями.

Уровень <span class="nk-severity nk-severity--error">error</span> влияет на код возврата, <span class="nk-severity nk-severity--warning">warning</span> и <span class="nk-severity nk-severity--info">info</span> — нет. Любое правило
отключается или переоценивается [профилем](../profiles.md).

## Структура отчёта

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`elements-order`](elements-order.md) | стандарт | ГОСТ 7.32-2017 п. 4<br>ГОСТ Р 2.105-2019 п. 6.1.1 | <span class="nk-severity nk-severity--error">error</span> | Структурные элементы идут не в установленном порядке |
| [`required-element-missing`](required-element-missing.md) | стандарт | ГОСТ 7.32-2017 п. 4<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--error">error</span> | Отсутствует обязательный структурный элемент |

## Заголовки и рубрикация

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`heading-depth`](heading-depth.md) | стандарт | ГОСТ 7.32-2017 п. 6.4.5<br>ГОСТ Р 2.105-2019 п. 6.5.9 | <span class="nk-severity nk-severity--warning">warning</span> | Глубина рубрикации превышает четыре уровня |
| [`heading-dot`](heading-dot.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.3<br>ГОСТ Р 2.105-2019 п. 6.6.2 | <span class="nk-severity nk-severity--error">error</span> | Заголовок заканчивается точкой |
| [`heading-empty`](heading-empty.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.2<br>ГОСТ Р 2.105-2019 п. 6.6.1 | <span class="nk-severity nk-severity--error">error</span> | Раздел или подраздел без заголовка |
| [`heading-hyphenation`](heading-hyphenation.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.4<br>ГОСТ Р 2.105-2019 п. 6.6.2 | <span class="nk-severity nk-severity--error">error</span> | В заголовке задан перенос слова |
| [`heading-rubric-word`](heading-rubric-word.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Заголовок начинается со слова «глава» или «раздел» |
| [`manual-section-number`](manual-section-number.md) | стандарт | ГОСТ 7.32-2017 п. 6.4.1<br>ГОСТ Р 2.105-2019 п. 6.5.4 | <span class="nk-severity nk-severity--error">error</span> | Номер раздела вписан в заголовок вручную |
| [`section-page-break`](section-page-break.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.1<br>ГОСТ Р 2.105-2019 п. 6.6.5 | <span class="nk-severity nk-severity--error">error</span> | Раздел не начинается с новой страницы |
| [`structural-heading-case`](structural-heading-case.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.1 | <span class="nk-severity nk-severity--error">error</span> | Заголовок структурного элемента набран не прописными буквами |
| [`structural-heading-numbered`](structural-heading-numbered.md) | стандарт | ГОСТ 7.32-2017 п. 6.2.1 | <span class="nk-severity nk-severity--error">error</span> | Заголовок структурного элемента пронумерован |

## Перечисления

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`enumeration-label`](enumeration-label.md) | стандарт | ГОСТ 7.32-2017 п. 6.4.6<br>ГОСТ Р 2.105-2019 п. 6.7.4 | <span class="nk-severity nk-severity--error">error</span> | Элемент перечисления обозначен не по форме |
| [`enumeration-letters`](enumeration-letters.md) | стандарт | ГОСТ 7.32-2017 п. 6.4.6<br>ГОСТ Р 2.105-2019 п. 6.7.5 | <span class="nk-severity nk-severity--error">error</span> | В перечислении использована недопустимая буква |
| [`enumeration-lowercase`](enumeration-lowercase.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.7.1 | <span class="nk-severity nk-severity--warning">warning</span> | Элемент перечисления начат с прописной буквы |
| [`enumeration-marker-nested`](enumeration-marker-nested.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.7.4 | <span class="nk-severity nk-severity--error">error</span> | Элемент маркированного списка разбит на подсписок |
| [`enumeration-marker-referenced`](enumeration-marker-referenced.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.7.4 | <span class="nk-severity nk-severity--error">error</span> | На элемент маркированного списка дана ссылка |
| [`enumeration-opening-colon`](enumeration-opening-colon.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.7.1 | <span class="nk-severity nk-severity--error">error</span> | Перед списком перечислений нет вводной формулировки с двоеточием |
| [`enumeration-single-item`](enumeration-single-item.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.7.1 | <span class="nk-severity nk-severity--error">error</span> | В списке перечислений меньше двух элементов |

## Реферат

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`abstract-text-position`](abstract-text-position.md) | стандарт | ГОСТ 7.32-2017 п. 6.12.3 | <span class="nk-severity nk-severity--error">error</span> | Текст реферата начинается до перечня ключевых слов |
| [`abstract-volume-info`](abstract-volume-info.md) | стандарт | ГОСТ 7.32-2017 п. 5.3.2 | <span class="nk-severity nk-severity--error">error</span> | В реферате нет сведений об объёме отчёта |
| [`abstract-volume-inline`](abstract-volume-inline.md) | стандарт | ГОСТ 7.32-2017 п. 6.12.1 | <span class="nk-severity nk-severity--error">error</span> | Сведения об объёме реферата приведены не в строку |
| [`keywords-count`](keywords-count.md) | стандарт | ГОСТ 7.32-2017 п. 5.3.2.1 | <span class="nk-severity nk-severity--error">error</span> | Число ключевых слов вне допустимого диапазона |
| [`keywords-final-dot`](keywords-final-dot.md) | стандарт | ГОСТ 7.32-2017 п. 6.12.2 | <span class="nk-severity nk-severity--error">error</span> | Перечень ключевых слов заканчивается точкой |
| [`keywords-uppercase`](keywords-uppercase.md) | стандарт | ГОСТ 7.32-2017 п. 6.12.2 | <span class="nk-severity nk-severity--error">error</span> | Ключевые слова набраны не прописными буквами |

## Термины и сокращения

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`abbreviations-dash`](abbreviations-dash.md) | стандарт | ГОСТ 7.32-2017 п. 6.15<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--warning">warning</span> | В перечне сокращений расшифровка отделена дефисом |
| [`abbreviations-final-punctuation`](abbreviations-final-punctuation.md) | стандарт | ГОСТ 7.32-2017 п. 6.15<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--warning">warning</span> | Запись перечня сокращений заканчивается знаком препинания |
| [`abbreviations-opening`](abbreviations-opening.md) | стандарт | ГОСТ 7.32-2017 п. 5.6.1<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--error">error</span> | Перечень сокращений не начинается с установленной фразы |
| [`abbreviations-order`](abbreviations-order.md) | стандарт | ГОСТ 7.32-2017 п. 6.15<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--error">error</span> | Сокращения в перечне идут не по алфавиту |
| [`terms-dash`](terms-dash.md) | стандарт | ГОСТ 7.32-2017 п. 6.14<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--warning">warning</span> | В перечне терминов определение отделено дефисом |
| [`terms-final-punctuation`](terms-final-punctuation.md) | стандарт | ГОСТ 7.32-2017 п. 6.14<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--warning">warning</span> | Запись перечня терминов заканчивается знаком препинания |
| [`terms-opening`](terms-opening.md) | стандарт | ГОСТ 7.32-2017 п. 5.5.2<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--error">error</span> | Перечень терминов не начинается с установленной фразы |
| [`terms-order`](terms-order.md) | стандарт | ГОСТ 7.32-2017 п. 6.14<br>ГОСТ Р 2.105-2019 п. 6.1.2 | <span class="nk-severity nk-severity--error">error</span> | Термины в перечне идут не по алфавиту |

## Иллюстрации

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`figure-appendix-numbering`](figure-appendix-numbering.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.5<br>ГОСТ Р 2.105-2019 п. 6.9.3 | <span class="nk-severity nk-severity--error">error</span> | Иллюстрация приложения нумеруется без его обозначения |
| [`figure-caption-capital`](figure-caption-capital.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.8 | <span class="nk-severity nk-severity--error">error</span> | Наименование рисунка начинается со строчной буквы |
| [`figure-caption-dot`](figure-caption-dot.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.7 | <span class="nk-severity nk-severity--error">error</span> | Наименование рисунка заканчивается точкой |
| [`figure-caption-hyphenation`](figure-caption-hyphenation.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.8 | <span class="nk-severity nk-severity--error">error</span> | В наименовании рисунка задан перенос слова |
| [`figure-caption-manual-number`](figure-caption-manual-number.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.7<br>ГОСТ Р 2.105-2019 п. 6.9.3 | <span class="nk-severity nk-severity--error">error</span> | Номер рисунка вписан в наименование вручную |
| [`figure-caption-position`](figure-caption-position.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.7<br>ГОСТ Р 2.105-2019 п. 6.9.4 | <span class="nk-severity nk-severity--error">error</span> | Наименование рисунка расположено выше изображения |
| [`figure-no-reference`](figure-no-reference.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.1<br>ГОСТ Р 2.105-2019 п. 6.9.3 | <span class="nk-severity nk-severity--error">error</span> | На рисунок нет ссылки в тексте |
| [`figure-numbering-scheme-mixed`](figure-numbering-scheme-mixed.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.4<br>ГОСТ Р 2.105-2019 п. 6.9.3 | <span class="nk-severity nk-severity--error">error</span> | Схема нумерации иллюстраций задана в документе несколько раз |
| [`figure-position`](figure-position.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.1<br>ГОСТ Р 2.105-2019 п. 6.9.1 | <span class="nk-severity nk-severity--error">error</span> | Иллюстрация размещена выше первой ссылки на неё |
| [`figure-reference-form`](figure-reference-form.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Ссылка на графический материал дана не установленным оборотом |
| [`figure-reference-word`](figure-reference-word.md) | стандарт | ГОСТ 7.32-2017 п. 6.5.1<br>ГОСТ Р 2.105-2019 п. 6.9.3 | <span class="nk-severity nk-severity--warning">warning</span> | В ссылке на иллюстрацию использовано сокращение «рис.» |

## Таблицы

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`table-appendix-numbering`](table-appendix-numbering.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.4<br>ГОСТ Р 2.105-2019 п. 6.8.2 | <span class="nk-severity nk-severity--error">error</span> | Таблица приложения нумеруется без его обозначения |
| [`table-caption-capital`](table-caption-capital.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.3 | <span class="nk-severity nk-severity--error">error</span> | Наименование таблицы начинается со строчной буквы |
| [`table-caption-dot`](table-caption-dot.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.3 | <span class="nk-severity nk-severity--error">error</span> | Наименование таблицы заканчивается точкой |
| [`table-caption-manual-number`](table-caption-manual-number.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.3<br>ГОСТ Р 2.105-2019 п. 6.8.2 | <span class="nk-severity nk-severity--error">error</span> | Номер таблицы вписан в наименование вручную |
| [`table-caption-position`](table-caption-position.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.3<br>ГОСТ Р 2.105-2019 п. 6.8.1 | <span class="nk-severity nk-severity--error">error</span> | Наименование таблицы расположено ниже самой таблицы |
| [`table-continuation`](table-continuation.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.3 | <span class="nk-severity nk-severity--warning">warning</span> | Над продолжением таблицы нет надписи «Продолжение таблицы» |
| [`table-diagonal`](table-diagonal.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.6<br>ГОСТ Р 2.105-2019 п. 6.8.5 | <span class="nk-severity nk-severity--error">error</span> | Шапка таблицы разделена диагональной линией |
| [`table-empty-cell`](table-empty-cell.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.8.19 | <span class="nk-severity nk-severity--warning">warning</span> | Графа таблицы оставлена пустой |
| [`table-no-reference`](table-no-reference.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.2<br>ГОСТ Р 2.105-2019 п. 6.8.3 | <span class="nk-severity nk-severity--error">error</span> | На таблицу нет ссылки в тексте |
| [`table-position`](table-position.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.2<br>ГОСТ Р 2.105-2019 п. 6.8.6 | <span class="nk-severity nk-severity--error">error</span> | Таблица размещена выше первой ссылки на неё |
| [`table-reference-word`](table-reference-word.md) | стандарт | ГОСТ 7.32-2017 п. 6.6.2<br>ГОСТ Р 2.105-2019 п. 6.8.3 | <span class="nk-severity nk-severity--warning">warning</span> | В ссылке на таблицу использовано сокращение «табл.» |
| [`table-too-small`](table-too-small.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.8.1 | <span class="nk-severity nk-severity--error">error</span> | В таблице меньше двух граф или двух строк |

## Формулы

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`formula-appendix-numbering`](formula-appendix-numbering.md) | стандарт | ГОСТ 7.32-2017 п. 6.8.5<br>ГОСТ Р 2.105-2019 п. 6.10.4 | <span class="nk-severity nk-severity--error">error</span> | Формула приложения нумеруется без обозначения приложения |
| [`formula-blank-line-around`](formula-blank-line-around.md) | стандарт | ГОСТ 7.32-2017 п. 6.8.1 | <span class="nk-severity nk-severity--error">error</span> | Формула не отделена свободной строкой |
| [`formula-no-reference`](formula-no-reference.md) | стандарт | ГОСТ 7.32-2017 п. 6.8.3 | <span class="nk-severity nk-severity--warning">warning</span> | Формула пронумерована, но ссылки на неё нет |
| [`formula-reference-format`](formula-reference-format.md) | стандарт | ГОСТ 7.32-2017 п. 6.8.4<br>ГОСТ Р 2.105-2019 п. 6.10.4 | <span class="nk-severity nk-severity--error">error</span> | Номер формулы в ссылке приведён без скобок |
| [`formula-sequence-comma`](formula-sequence-comma.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.10.1 | <span class="nk-severity nk-severity--warning">warning</span> | Формулы идут подряд без разделяющего знака |
| [`formula-where-colon`](formula-where-colon.md) | стандарт | ГОСТ 7.32-2017 п. 6.8.2<br>ГОСТ Р 2.105-2019 п. 6.10.1 | <span class="nk-severity nk-severity--error">error</span> | Пояснение к формуле начинается со слова «где» с двоеточием |

## Примечания и сноски

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`footnote-space`](footnote-space.md) | стандарт | ГОСТ 7.32-2017 п. 6.7.4<br>ГОСТ Р 2.105-2019 п. 6.13.3 | <span class="nk-severity nk-severity--error">error</span> | Знак сноски отделён пробелом от поясняемого слова |
| [`note-capital`](note-capital.md) | стандарт | ГОСТ 7.32-2017 п. 6.7.2<br>ГОСТ Р 2.105-2019 п. 6.12.2 | <span class="nk-severity nk-severity--error">error</span> | Слово «Примечание» набрано со строчной буквы |
| [`note-dash`](note-dash.md) | стандарт | ГОСТ 7.32-2017 п. 6.7.3<br>ГОСТ Р 2.105-2019 п. 6.12.3 | <span class="nk-severity nk-severity--error">error</span> | После слова «Примечание» стоит не тире |

## Источники и ссылки на них

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`bibitem-area-separator`](bibitem-area-separator.md) | стандарт | ГОСТ Р 7.0.100-2018 п. 4.6.2 | <span class="nk-severity nk-severity--error">error</span> | Области описания разделены не знаком «точка и тире» |
| [`bibitem-final-dot`](bibitem-final-dot.md) | стандарт | ГОСТ Р 7.0.100-2018 п. 4.6.1 | <span class="nk-severity nk-severity--error">error</span> | Библиографическое описание не заканчивается точкой |
| [`bibitem-prescribed-spacing`](bibitem-prescribed-spacing.md) | стандарт | ГОСТ Р 7.0.100-2018 п. 4.6.5 | <span class="nk-severity nk-severity--error">error</span> | У знака предписанной пунктуации нет пробела |
| [`bibitem-uncited`](bibitem-uncited.md) | стандарт | ГОСТ 7.32-2017 п. 6.16<br>ГОСТ Р 2.105-2019 п. 6.4.2 | <span class="nk-severity nk-severity--warning">warning</span> | На запись списка источников нет ссылок в тексте |
| [`bibitem-url-access-date`](bibitem-url-access-date.md) | стандарт | ГОСТ Р 7.0.100-2018 п. 5.8.6.4 | <span class="nk-severity nk-severity--error">error</span> | У электронного адреса нет даты обращения |
| [`bibitem-url-prefix`](bibitem-url-prefix.md) | стандарт | ГОСТ Р 7.0.100-2018 п. 5.8.6.4 | <span class="nk-severity nk-severity--error">error</span> | Электронный адрес приведён без аббревиатуры URL |
| [`bibliography-order`](bibliography-order.md) | стандарт | ГОСТ 7.32-2017 п. 6.16<br>ГОСТ Р 2.105-2019 п. 6.4.2 | <span class="nk-severity nk-severity--error">error</span> | Записи списка источников идут не в порядке появления ссылок |
| [`bibtex-order-unverifiable`](bibtex-order-unverifiable.md) | стандарт | ГОСТ 7.32-2017 п. 6.16<br>ГОСТ Р 2.105-2019 п. 6.4.2 | <span class="nk-severity nk-severity--info">info</span> | Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется |
| [`cite-unresolved`](cite-unresolved.md) | стандарт | ГОСТ 7.32-2017 п. 6.9.1<br>ГОСТ Р 2.105-2019 п. 6.4.2 | <span class="nk-severity nk-severity--error">error</span> | Ссылка указывает на отсутствующую запись списка источников |

## Приложения

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`appendix-internal-numbering`](appendix-internal-numbering.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.6<br>ГОСТ Р 2.105-2019 п. 6.3.7 | <span class="nk-severity nk-severity--error">error</span> | Рубрика внутри приложения нумеруется без его обозначения |
| [`appendix-letter`](appendix-letter.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.4<br>ГОСТ Р 2.105-2019 п. 6.3.5 | <span class="nk-severity nk-severity--error">error</span> | Приложение обозначено недопустимой буквой |
| [`appendix-no-reference`](appendix-no-reference.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.2<br>ГОСТ Р 2.105-2019 п. 6.3.3 | <span class="nk-severity nk-severity--error">error</span> | На приложение нет ссылки в тексте |
| [`appendix-order`](appendix-order.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.2<br>ГОСТ Р 2.105-2019 п. 6.3.3 | <span class="nk-severity nk-severity--error">error</span> | Приложения идут не в порядке ссылок на них |
| [`appendix-page-break`](appendix-page-break.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.3<br>ГОСТ Р 2.105-2019 п. 6.3.4 | <span class="nk-severity nk-severity--error">error</span> | Приложение не начинается с новой страницы |
| [`appendix-sequence`](appendix-sequence.md) | стандарт | ГОСТ 7.32-2017 п. 6.17.4<br>ГОСТ Р 2.105-2019 п. 6.3.5 | <span class="nk-severity nk-severity--error">error</span> | В обозначениях приложений пропущена буква |
| [`appendix-status`](appendix-status.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.3.4 | <span class="nk-severity nk-severity--error">error</span> | Под обозначением приложения не указан его статус |

## Изложение текста

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`evaluative-word`](evaluative-word.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Свойство названо оценкой, а не показателем |
| [`first-person-pronoun`](first-person-pronoun.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Текст изложен от первого лица: местоимение |
| [`first-person-verb`](first-person-verb.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Текст изложен от первого лица: глагол |
| [`math-sign-without-value`](math-sign-without-value.md) | стандарт | ГОСТ Р 2.105-2019 п. 5.2.4 | <span class="nk-severity nk-severity--warning">warning</span> | Математический знак приведён без числового значения |
| [`sign-instead-of-word`](sign-instead-of-word.md) | стандарт | ГОСТ Р 2.105-2019 п. 5.2.4 | <span class="nk-severity nk-severity--warning">warning</span> | Знак приведён вместо слова |
| [`standard-without-number`](standard-without-number.md) | стандарт | ГОСТ Р 2.105-2019 п. 5.2.4 | <span class="nk-severity nk-severity--warning">warning</span> | Обозначение стандарта приведено без регистрационного номера |
| [`unit-in-range`](unit-in-range.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.16.5 | <span class="nk-severity nk-severity--warning">warning</span> | Единица величины повторена при обеих границах диапазона |
| [`unit-in-series`](unit-in-series.md) | стандарт | ГОСТ Р 2.105-2019 п. 6.16.4 | <span class="nk-severity nk-severity--warning">warning</span> | Единица величины повторена при каждом значении ряда |
| [`vague-quantifier`](vague-quantifier.md) | положение вуза | — | <span class="nk-severity nk-severity--warning">warning</span> | Мера приведена без числа |

## Типографика

| ID | Источник | Пункты | Уровень | Название |
|---|---|---|---|---|
| [`initials-nbsp`](initials-nbsp.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Инициалы не привязаны к фамилии |
| [`particle-nbsp`](particle-nbsp.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Частица не привязана к предыдущему слову |
| [`preposition-nbsp`](preposition-nbsp.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Предлог не привязан к следующему слову |
| [`reference-nbsp`](reference-nbsp.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Номер в ссылке отделён разрывным пробелом |
| [`text-dash`](text-dash.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Дефис вместо тире |
| [`text-quotes`](text-quotes.md) | общее | — | <span class="nk-severity nk-severity--info">info</span> | Прямые кавычки вместо «ёлочек» |
| [`unit-nbsp`](unit-nbsp.md) | общее | ГОСТ Р 2.105-2019 п. 6.16.6 | <span class="nk-severity nk-severity--info">info</span> | Число не привязано к единице измерения |
