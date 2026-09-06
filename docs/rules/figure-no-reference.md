# figure-no-reference

**На рисунок нет ссылки в тексте.**

| | |
|---|---|
| Категория | Иллюстрации |
| Пункты | ГОСТ 7.32-2017 п. 6.5.1 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.figures.figure_reference` |
| Фикстуры | `tests/fixtures/figure-no-reference/` |
| Автоисправление | нет |

Собирает метки рисунков и ссылки на них в тексте. Находка выдаётся на рисунок
без ссылки, а также на рисунок без метки — сослаться на него нечем.

## Почему это нарушение

На все иллюстрации в отчёте должны быть даны ссылки со словом «рисунок»
и номером: иллюстрация поясняет текст, а не существует отдельно от него.
По ссылкам определяется и порядок размещения иллюстраций.

## Как исправить

Добавить `\label` после `\caption` и сослаться на рисунок в том абзаце,
который он поясняет.

## Нарушение

```latex
Текст без единой ссылки на иллюстрации.

\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{Зависимость погрешности от числа измерений}
\end{figure}
```

## Как правильно

```latex
Схема установки приведена на рисунке~\ref{fig:setup}, результаты — на
рисунке~\ref{fig:plot}.

\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{Зависимость погрешности от числа измерений}
  \label{fig:plot}
\end{figure}

Погрешность метода обсуждается ниже\footnote{см. рисунок~\ref{fig:error}}.

\begin{figure}
  \includegraphics{img/error.png}
  \caption{Распределение погрешности\label{fig:error}}
\end{figure}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["figure-no-reference"]

[rules."figure-no-reference"]
severity = "info"
```
