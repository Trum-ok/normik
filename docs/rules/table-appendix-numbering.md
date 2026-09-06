# table-appendix-numbering

**Таблица приложения нумеруется без его обозначения.**

| | |
|---|---|
| Категория | Таблицы |
| Пункты | ГОСТ 7.32-2017 п. 6.6.4, ГОСТ Р 2.105-2019 п. 6.8.2 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.tables.appendix_table_numbering` |
| Фикстуры | `tests/fixtures/table-appendix-numbering/` |
| Автоисправление | нет |

Проверяет, что таблицы внутри приложения нумеруются с его обозначением.

## Почему это нарушение

Нумерация в приложении отдельная: она начинается заново и несёт обозначение
самого приложения. Сквозной номер из основной части ссылку «таблица А.1»
сделать не позволяет.

## Как исправить

Задать схему нумерации в пределах раздела — тогда внутри приложения номер
складывается из его буквы и порядкового номера.

## Нарушение

```latex
\section{Методика}

\begin{table}
  \caption{Результаты измерений}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\section*{ПРИЛОЖЕНИЕ А}

\begin{table}
  \caption{Вспомогательные данные}
  \begin{tabular}{ll}
    в & г \\
  \end{tabular}
\end{table}
```

## Как правильно

```latex
\counterwithin{table}{section}

\section{Методика}

\begin{table}
  \caption{Результаты измерений}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}

\section*{ПРИЛОЖЕНИЕ А}

\begin{table}
  \caption{Вспомогательные данные}
  \begin{tabular}{ll}
    в & г \\
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["table-appendix-numbering"]

[rules."table-appendix-numbering"]
severity = "info"
```
