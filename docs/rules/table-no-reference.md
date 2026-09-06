# table-no-reference

**На таблицу нет ссылки в тексте.**

| | |
|---|---|
| Категория | Таблицы |
| Пункты | ГОСТ 7.32-2017 п. 6.6.2 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.tables.table_reference` |
| Фикстуры | `tests/fixtures/table-no-reference/` |
| Автоисправление | нет |

Собирает метки таблиц и ссылки на них в тексте. Находка выдаётся на таблицу
без ссылки, а также на таблицу без метки.

## Почему это нарушение

На все таблицы в отчёте должны быть ссылки со словом «таблица» и её номером.
Таблица, на которую нет ссылки, не связана с изложением.

## Как исправить

Добавить `\label` после `\caption` и сослаться на таблицу в тексте.

## Нарушение

```latex
Текст без единой ссылки на таблицы.

\begin{table}
  \caption{Результаты измерений}
  \label{tab:results}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\begin{table}
  \caption{Сводка по этапам}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Как правильно

```latex
Результаты приведены в таблице~\ref{tab:results}, сводка — в
таблице~\ref{tab:summary}.

\begin{table}
  \caption{Результаты измерений}
  \label{tab:results}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\begin{table}
  \caption{Сводка по этапам}
  \label{tab:summary}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-no-reference"]

[rules."table-no-reference"]
severity = "info"
```
