# table-caption-capital

**Наименование таблицы начинается со строчной буквы.**

| | |
|---|---|
| Категория | Таблицы |
| Пункты | ГОСТ 7.32-2017 п. 6.6.3 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.tables.table_caption_capital` |
| Фикстуры | `tests/fixtures/table-caption-capital/` |
| Автоисправление | да, ключом `--fix` |

Проверяет первую букву наименования таблицы.

## Почему это нарушение

Наименование таблицы приводят с прописной буквы без точки в конце.

## Как исправить

Начать наименование с прописной буквы.

## Нарушение

```latex
\begin{table}
  \caption{результаты измерений погрешности}
  \label{tab:results}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\begin{table}
  \caption{метка внутри подписи\label{tab:inside}}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Как правильно

```latex
\begin{table}
  \caption{Результаты измерений погрешности}
  \label{tab:results}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-caption-capital"]

[rules."table-caption-capital"]
severity = "info"
```
