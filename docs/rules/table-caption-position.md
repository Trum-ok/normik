# table-caption-position

**Наименование таблицы расположено ниже самой таблицы.**

| | |
|---|---|
| Категория | Таблицы |
| Источник требования | стандарт |
| Пункты | ГОСТ 7.32-2017 п. 6.6.3<br>ГОСТ Р 2.105-2019 п. 6.8.1 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--error">error</span> |
| Объявлено в | `nk.rules.tables.table_caption_position` |
| Фикстуры | `tests/fixtures/table-caption-position/` |
| Автоисправление | нет |

Сравнивает положение `\caption` с началом самой таблицы внутри окружения.

## Почему это нарушение

Наименование помещают над таблицей слева, без абзацного отступа: читающий
должен понять, что перед ним, до того как начнёт разбирать головку.

## Как исправить

Перенести `\caption` выше начала таблицы.

## Нарушение

```latex
\begin{table}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
  \caption{Результаты измерений погрешности}
  \label{tab:results}
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

Подпись рисунка стоит ниже изображения — это её штатное место.

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{Зависимость погрешности}
\end{figure}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-caption-position"]

[rules."table-caption-position"]
severity = "info"
```
