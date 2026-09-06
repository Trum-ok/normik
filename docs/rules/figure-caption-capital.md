# figure-caption-capital

**Наименование рисунка начинается со строчной буквы.**

| | |
|---|---|
| Категория | Иллюстрации |
| Пункты | ГОСТ 7.32-2017 п. 6.5.8 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.figures.figure_caption_capital` |
| Фикстуры | `tests/fixtures/figure-caption-capital/` |
| Автоисправление | да, ключом `--fix` |

Проверяет первую букву наименования рисунка. Наименование, начинающееся
с цифры или обозначения, не проверяется.

## Почему это нарушение

Наименование рисунка приводят с прописной буквы без точки в конце.

## Как исправить

Начать наименование с прописной буквы.

## Нарушение

```latex
\begin{figure}
  \includegraphics{img/setup.png}
  \caption{схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{\textit{зависимость} погрешности от числа измерений}
  \label{fig:plot}
\end{figure}

\begin{figure}
  \includegraphics{img/inside.png}
  \caption{метка внутри подписи\label{fig:inside}}
\end{figure}
```

## Как правильно

```latex
\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{\textit{Зависимость} погрешности от числа измерений}
  \label{fig:plot}
\end{figure}

Наименование, начинающееся с формулы, правило не трогает.

\begin{figure}
  \includegraphics{img/formula.png}
  \caption{$E = mc^2$ в графическом виде}
  \label{fig:formula}
\end{figure}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["figure-caption-capital"]

[rules."figure-caption-capital"]
severity = "info"
```
