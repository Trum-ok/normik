# table-empty-cell

**Графа таблицы оставлена пустой.**

| | |
|---|---|
| Категория | Таблицы |
| Источник требования | стандарт |
| Пункты | ГОСТ Р 2.105-2019 п. 6.8.19 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--warning">warning</span> |
| Объявлено в | `nk.rules.tables.table_empty_cell` |
| Фикстуры | `tests/fixtures/table-empty-cell/` |
| Автоисправление | нет |

Ищет графы без содержимого. Строка с `\multicolumn` или `\multirow`
пропускается: объединённая ячейка оставляет пустые графы по построению,
и отличить их от забытых по исходнику нельзя.

## Почему это нарушение

Пустая графа читается двояко: то ли данных нет, то ли их забыли внести.
Прочерк говорит, что данных нет, и снимает вопрос.

## Как исправить

Поставить в пустую графу тире.

## Нарушение

```latex
\begin{table}
  \caption{Показатели изделия}
  \begin{tabular}{ll}
    \hline
    Показатель & Значение \\
    \hline
    Масса, кг &  \\
    Длина, мм & 340 \\
    \hline
  \end{tabular}
\end{table}
```

## Как правильно

```latex
\begin{table}
  \caption{Показатели изделия}
  \begin{tabular}{ll}
    \hline
    Показатель & Значение \\
    \hline
    Масса, кг & — \\
    Длина, мм & 340 \\
    \hline
  \end{tabular}
\end{table}

Объединённая ячейка пустых граф не считает:

\begin{table}
  \caption{Сводка}
  \begin{tabular}{ll}
    \hline
    \multicolumn{2}{c}{Итог} \\
    Масса, кг & 12,5 \\
    \hline
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-empty-cell"]

[rules."table-empty-cell"]
severity = "info"
```
