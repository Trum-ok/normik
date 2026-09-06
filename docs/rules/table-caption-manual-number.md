# table-caption-manual-number

**Номер таблицы вписан в наименование вручную.**

| | |
|---|---|
| Категория | Таблицы |
| Пункты | ГОСТ 7.32-2017 п. 6.6.3<br>ГОСТ Р 2.105-2019 п. 6.8.2 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--error">error</span> |
| Объявлено в | `nk.rules.tables.table_caption_manual_number` |
| Фикстуры | `tests/fixtures/table-caption-manual-number/` |
| Автоисправление | да, ключом `--fix` |

Ищет наименования, начинающиеся со слова «Таблица» или сокращения «Табл.»
с номером.

## Почему это нарушение

Слово «Таблица», номер и тире подставляются автоматически. Вписанный руками
номер удваивает подпись и расходится с автоматической нумерацией.

## Как исправить

Оставить в `\caption` только текст наименования.

## Нарушение

```latex
\begin{table}
  \caption{Таблица 1 — Результаты измерений}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\begin{table}
  \caption{Табл. 2.3 - Сводка по этапам}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\begin{table}
  \caption{Таблица 4 — Метка внутри подписи\label{tab:inside}}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Как правильно

```latex
\begin{table}
  \caption{Результаты измерений}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

Слово «таблица» без номера в начале наименования нарушением не является.

\begin{table}
  \caption{Таблицы сравнения по двум методикам}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-caption-manual-number"]

[rules."table-caption-manual-number"]
severity = "info"
```
