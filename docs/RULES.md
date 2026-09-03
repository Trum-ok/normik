# Правила

Файл создаётся командой `nk rules docs` и руками не редактируется.

Идентификатор правила состоит из префикса `G732`, пункта ГОСТ 7.32-2017
и мнемонического суффикса: на один пункт стандарта может приходиться
несколько независимых проверок.


## Сводка

| ID | Пункт | Уровень | Название |
|---|---|---|---|
| [G732-4-elements-order](#g732-4-elements-order) | 4 | error | Структурные элементы идут не в установленном порядке |
| [G732-4-required-element-missing](#g732-4-required-element-missing) | 4 | error | Отсутствует обязательный структурный элемент |
| [G732-5.3.2-abstract-volume-info](#g732-532-abstract-volume-info) | 5.3.2 | error | В реферате нет сведений об объёме отчёта |
| [G732-5.3.2.1-keywords-count](#g732-5321-keywords-count) | 5.3.2.1 | error | Число ключевых слов вне допустимого диапазона |
| [G732-5.5.2-terms-opening](#g732-552-terms-opening) | 5.5.2 | error | Перечень терминов не начинается с установленной фразы |
| [G732-5.6.1-abbreviations-opening](#g732-561-abbreviations-opening) | 5.6.1 | error | Перечень сокращений не начинается с установленной фразы |
| [G732-6.2.1-structural-heading-case](#g732-621-structural-heading-case) | 6.2.1 | error | Заголовок структурного элемента набран не прописными буквами |
| [G732-6.2.1-structural-heading-numbered](#g732-621-structural-heading-numbered) | 6.2.1 | error | Заголовок структурного элемента пронумерован |
| [G732-6.2.2-heading-empty](#g732-622-heading-empty) | 6.2.2 | error | Раздел или подраздел без заголовка |
| [G732-6.2.3-heading-dot](#g732-623-heading-dot) | 6.2.3 | error | Заголовок заканчивается точкой |
| [G732-6.2.4-heading-hyphenation](#g732-624-heading-hyphenation) | 6.2.4 | error | В заголовке задан перенос слова |
| [G732-6.4.1-manual-section-number](#g732-641-manual-section-number) | 6.4.1 | error | Номер раздела вписан в заголовок вручную |
| [G732-6.4.5-heading-depth](#g732-645-heading-depth) | 6.4.5 | warning | Глубина рубрикации превышает четыре уровня |
| [G732-6.4.6-enumeration-letters](#g732-646-enumeration-letters) | 6.4.6 | error | В перечислении использована недопустимая буква |
| [G732-6.5.1-figure-no-reference](#g732-651-figure-no-reference) | 6.5.1 | error | На рисунок нет ссылки в тексте |
| [G732-6.5.1-reference-word](#g732-651-reference-word) | 6.5.1 | warning | В ссылке на иллюстрацию использовано сокращение «рис.» |
| [G732-6.5.7-caption-dot](#g732-657-caption-dot) | 6.5.7 | error | Наименование рисунка заканчивается точкой |
| [G732-6.5.7-caption-manual-number](#g732-657-caption-manual-number) | 6.5.7 | error | Номер рисунка вписан в наименование вручную |
| [G732-6.5.7-caption-position](#g732-657-caption-position) | 6.5.7 | error | Наименование рисунка расположено выше изображения |
| [G732-6.5.8-caption-capital](#g732-658-caption-capital) | 6.5.8 | error | Наименование рисунка начинается со строчной буквы |
| [G732-6.5.8-caption-hyphenation](#g732-658-caption-hyphenation) | 6.5.8 | error | В наименовании рисунка задан перенос слова |
| [G732-6.6.2-reference-word](#g732-662-reference-word) | 6.6.2 | warning | В ссылке на таблицу использовано сокращение «табл.» |
| [G732-6.6.2-table-no-reference](#g732-662-table-no-reference) | 6.6.2 | error | На таблицу нет ссылки в тексте |
| [G732-6.6.3-caption-capital](#g732-663-caption-capital) | 6.6.3 | error | Наименование таблицы начинается со строчной буквы |
| [G732-6.6.3-caption-dot](#g732-663-caption-dot) | 6.6.3 | error | Наименование таблицы заканчивается точкой |
| [G732-6.6.3-caption-manual-number](#g732-663-caption-manual-number) | 6.6.3 | error | Номер таблицы вписан в наименование вручную |
| [G732-6.6.3-caption-position](#g732-663-caption-position) | 6.6.3 | error | Наименование таблицы расположено ниже самой таблицы |
| [G732-6.8.1-blank-line-around](#g732-681-blank-line-around) | 6.8.1 | error | Формула не отделена свободной строкой |
| [G732-6.8.2-where-colon](#g732-682-where-colon) | 6.8.2 | error | Пояснение к формуле начинается со слова «где» с двоеточием |
| [G732-6.8.3-formula-no-reference](#g732-683-formula-no-reference) | 6.8.3 | warning | Формула пронумерована, но ссылки на неё нет |
| [G732-6.8.4-formula-reference-format](#g732-684-formula-reference-format) | 6.8.4 | error | Номер формулы в ссылке приведён без скобок |
| [G732-6.9.1-cite-unresolved](#g732-691-cite-unresolved) | 6.9.1 | error | Ссылка указывает на отсутствующую запись списка источников |
| [G732-6.12.2-keywords-final-dot](#g732-6122-keywords-final-dot) | 6.12.2 | error | Перечень ключевых слов заканчивается точкой |
| [G732-6.12.2-keywords-uppercase](#g732-6122-keywords-uppercase) | 6.12.2 | error | Ключевые слова набраны не прописными буквами |
| [G732-6.16-bibitem-uncited](#g732-616-bibitem-uncited) | 6.16 | warning | На запись списка источников нет ссылок в тексте |
| [G732-6.16-bibliography-order](#g732-616-bibliography-order) | 6.16 | error | Записи списка источников идут не в порядке появления ссылок |
| [G732-6.16-bibtex-order-unverifiable](#g732-616-bibtex-order-unverifiable) | 6.16 | info | Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется |
| [G732-6.17.2-appendix-no-reference](#g732-6172-appendix-no-reference) | 6.17.2 | error | На приложение нет ссылки в тексте |
| [G732-6.17.4-appendix-letter](#g732-6174-appendix-letter) | 6.17.4 | error | Приложение обозначено недопустимой буквой |
| [G732-6.17.4-appendix-sequence](#g732-6174-appendix-sequence) | 6.17.4 | error | В обозначениях приложений пропущена буква |

## Правила

### G732-4-elements-order

Структурные элементы идут не в установленном порядке.

- пункт ГОСТ 7.32-2017: 4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.elements_order`
- фикстуры: `tests/fixtures/G732-4-elements-order/`

### G732-4-required-element-missing

Отсутствует обязательный структурный элемент.

- пункт ГОСТ 7.32-2017: 4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.required_elements`
- фикстуры: `tests/fixtures/G732-4-required-element-missing/`

### G732-5.3.2-abstract-volume-info

В реферате нет сведений об объёме отчёта.

- пункт ГОСТ 7.32-2017: 5.3.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.abstract_volume_info`
- фикстуры: `tests/fixtures/G732-5.3.2-abstract-volume-info/`

### G732-5.3.2.1-keywords-count

Число ключевых слов вне допустимого диапазона.

- пункт ГОСТ 7.32-2017: 5.3.2.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.keywords_count`
- фикстуры: `tests/fixtures/G732-5.3.2.1-keywords-count/`
- параметры: `keywords_max = 15`, `keywords_min = 5`

### G732-5.5.2-terms-opening

Перечень терминов не начинается с установленной фразы.

- пункт ГОСТ 7.32-2017: 5.5.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.terms_opening`
- фикстуры: `tests/fixtures/G732-5.5.2-terms-opening/`

### G732-5.6.1-abbreviations-opening

Перечень сокращений не начинается с установленной фразы.

- пункт ГОСТ 7.32-2017: 5.6.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.abbreviations_opening`
- фикстуры: `tests/fixtures/G732-5.6.1-abbreviations-opening/`

### G732-6.2.1-structural-heading-case

Заголовок структурного элемента набран не прописными буквами.

- пункт ГОСТ 7.32-2017: 6.2.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.structural_heading_case`
- фикстуры: `tests/fixtures/G732-6.2.1-structural-heading-case/`

### G732-6.2.1-structural-heading-numbered

Заголовок структурного элемента пронумерован.

- пункт ГОСТ 7.32-2017: 6.2.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.structural_heading_numbered`
- фикстуры: `tests/fixtures/G732-6.2.1-structural-heading-numbered/`

### G732-6.2.2-heading-empty

Раздел или подраздел без заголовка.

- пункт ГОСТ 7.32-2017: 6.2.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.heading_empty`
- фикстуры: `tests/fixtures/G732-6.2.2-heading-empty/`

### G732-6.2.3-heading-dot

Заголовок заканчивается точкой.

- пункт ГОСТ 7.32-2017: 6.2.3
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.heading_dot`
- фикстуры: `tests/fixtures/G732-6.2.3-heading-dot/`

### G732-6.2.4-heading-hyphenation

В заголовке задан перенос слова.

- пункт ГОСТ 7.32-2017: 6.2.4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.heading_hyphenation`
- фикстуры: `tests/fixtures/G732-6.2.4-heading-hyphenation/`

### G732-6.4.1-manual-section-number

Номер раздела вписан в заголовок вручную.

- пункт ГОСТ 7.32-2017: 6.4.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.manual_section_number`
- фикстуры: `tests/fixtures/G732-6.4.1-manual-section-number/`

### G732-6.4.5-heading-depth

Глубина рубрикации превышает четыре уровня.

- пункт ГОСТ 7.32-2017: 6.4.5
- уровень по умолчанию: `warning`
- объявлено в: `nk.rules.layout.heading_depth`
- фикстуры: `tests/fixtures/G732-6.4.5-heading-depth/`
- параметры: `max_depth = 4`

### G732-6.4.6-enumeration-letters

В перечислении использована недопустимая буква.

- пункт ГОСТ 7.32-2017: 6.4.6
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.layout.enumeration_letters`
- фикстуры: `tests/fixtures/G732-6.4.6-enumeration-letters/`

### G732-6.5.1-figure-no-reference

На рисунок нет ссылки в тексте.

- пункт ГОСТ 7.32-2017: 6.5.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_reference`
- фикстуры: `tests/fixtures/G732-6.5.1-figure-no-reference/`

### G732-6.5.1-reference-word

В ссылке на иллюстрацию использовано сокращение «рис.».

- пункт ГОСТ 7.32-2017: 6.5.1
- уровень по умолчанию: `warning`
- объявлено в: `nk.rules.elements.figure_reference_word`
- фикстуры: `tests/fixtures/G732-6.5.1-reference-word/`

### G732-6.5.7-caption-dot

Наименование рисунка заканчивается точкой.

- пункт ГОСТ 7.32-2017: 6.5.7
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_caption_dot`
- фикстуры: `tests/fixtures/G732-6.5.7-caption-dot/`

### G732-6.5.7-caption-manual-number

Номер рисунка вписан в наименование вручную.

- пункт ГОСТ 7.32-2017: 6.5.7
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_caption_manual_number`
- фикстуры: `tests/fixtures/G732-6.5.7-caption-manual-number/`

### G732-6.5.7-caption-position

Наименование рисунка расположено выше изображения.

- пункт ГОСТ 7.32-2017: 6.5.7
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_caption_position`
- фикстуры: `tests/fixtures/G732-6.5.7-caption-position/`

### G732-6.5.8-caption-capital

Наименование рисунка начинается со строчной буквы.

- пункт ГОСТ 7.32-2017: 6.5.8
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_caption_capital`
- фикстуры: `tests/fixtures/G732-6.5.8-caption-capital/`

### G732-6.5.8-caption-hyphenation

В наименовании рисунка задан перенос слова.

- пункт ГОСТ 7.32-2017: 6.5.8
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.figure_caption_hyphenation`
- фикстуры: `tests/fixtures/G732-6.5.8-caption-hyphenation/`

### G732-6.6.2-reference-word

В ссылке на таблицу использовано сокращение «табл.».

- пункт ГОСТ 7.32-2017: 6.6.2
- уровень по умолчанию: `warning`
- объявлено в: `nk.rules.elements.table_reference_word`
- фикстуры: `tests/fixtures/G732-6.6.2-reference-word/`

### G732-6.6.2-table-no-reference

На таблицу нет ссылки в тексте.

- пункт ГОСТ 7.32-2017: 6.6.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.table_reference`
- фикстуры: `tests/fixtures/G732-6.6.2-table-no-reference/`

### G732-6.6.3-caption-capital

Наименование таблицы начинается со строчной буквы.

- пункт ГОСТ 7.32-2017: 6.6.3
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.table_caption_capital`
- фикстуры: `tests/fixtures/G732-6.6.3-caption-capital/`

### G732-6.6.3-caption-dot

Наименование таблицы заканчивается точкой.

- пункт ГОСТ 7.32-2017: 6.6.3
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.table_caption_dot`
- фикстуры: `tests/fixtures/G732-6.6.3-caption-dot/`

### G732-6.6.3-caption-manual-number

Номер таблицы вписан в наименование вручную.

- пункт ГОСТ 7.32-2017: 6.6.3
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.table_caption_manual_number`
- фикстуры: `tests/fixtures/G732-6.6.3-caption-manual-number/`

### G732-6.6.3-caption-position

Наименование таблицы расположено ниже самой таблицы.

- пункт ГОСТ 7.32-2017: 6.6.3
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.table_caption_position`
- фикстуры: `tests/fixtures/G732-6.6.3-caption-position/`

### G732-6.8.1-blank-line-around

Формула не отделена свободной строкой.

- пункт ГОСТ 7.32-2017: 6.8.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.formula_blank_lines`
- фикстуры: `tests/fixtures/G732-6.8.1-blank-line-around/`

### G732-6.8.2-where-colon

Пояснение к формуле начинается со слова «где» с двоеточием.

- пункт ГОСТ 7.32-2017: 6.8.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.formula_where_colon`
- фикстуры: `tests/fixtures/G732-6.8.2-where-colon/`

### G732-6.8.3-formula-no-reference

Формула пронумерована, но ссылки на неё нет.

- пункт ГОСТ 7.32-2017: 6.8.3
- уровень по умолчанию: `warning`
- объявлено в: `nk.rules.elements.formula_reference`
- фикстуры: `tests/fixtures/G732-6.8.3-formula-no-reference/`

### G732-6.8.4-formula-reference-format

Номер формулы в ссылке приведён без скобок.

- пункт ГОСТ 7.32-2017: 6.8.4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.formula_reference_format`
- фикстуры: `tests/fixtures/G732-6.8.4-formula-reference-format/`

### G732-6.9.1-cite-unresolved

Ссылка указывает на отсутствующую запись списка источников.

- пункт ГОСТ 7.32-2017: 6.9.1
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.bibliography_cite_unresolved`
- фикстуры: `tests/fixtures/G732-6.9.1-cite-unresolved/`

### G732-6.12.2-keywords-final-dot

Перечень ключевых слов заканчивается точкой.

- пункт ГОСТ 7.32-2017: 6.12.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.keywords_final_dot`
- фикстуры: `tests/fixtures/G732-6.12.2-keywords-final-dot/`

### G732-6.12.2-keywords-uppercase

Ключевые слова набраны не прописными буквами.

- пункт ГОСТ 7.32-2017: 6.12.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.keywords_uppercase`
- фикстуры: `tests/fixtures/G732-6.12.2-keywords-uppercase/`

### G732-6.16-bibitem-uncited

На запись списка источников нет ссылок в тексте.

- пункт ГОСТ 7.32-2017: 6.16
- уровень по умолчанию: `warning`
- объявлено в: `nk.rules.elements.bibliography_uncited`
- фикстуры: `tests/fixtures/G732-6.16-bibitem-uncited/`

### G732-6.16-bibliography-order

Записи списка источников идут не в порядке появления ссылок.

- пункт ГОСТ 7.32-2017: 6.16
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.elements.bibliography_order`
- фикстуры: `tests/fixtures/G732-6.16-bibliography-order/`

### G732-6.16-bibtex-order-unverifiable

Порядок записей библиографии задан стилем BibTeX и по исходникам не проверяется.

- пункт ГОСТ 7.32-2017: 6.16
- уровень по умолчанию: `info`
- объявлено в: `nk.rules.elements.bibliography_bibtex`
- фикстуры: `tests/fixtures/G732-6.16-bibtex-order-unverifiable/`

### G732-6.17.2-appendix-no-reference

На приложение нет ссылки в тексте.

- пункт ГОСТ 7.32-2017: 6.17.2
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.appendix_reference`
- фикстуры: `tests/fixtures/G732-6.17.2-appendix-no-reference/`

### G732-6.17.4-appendix-letter

Приложение обозначено недопустимой буквой.

- пункт ГОСТ 7.32-2017: 6.17.4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.appendix_letter`
- фикстуры: `tests/fixtures/G732-6.17.4-appendix-letter/`

### G732-6.17.4-appendix-sequence

В обозначениях приложений пропущена буква.

- пункт ГОСТ 7.32-2017: 6.17.4
- уровень по умолчанию: `error`
- объявлено в: `nk.rules.structure.appendix_sequence`
- фикстуры: `tests/fixtures/G732-6.17.4-appendix-sequence/`
