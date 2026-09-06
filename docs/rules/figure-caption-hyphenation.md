# figure-caption-hyphenation

**В наименовании рисунка задан перенос слова.**

| | |
|---|---|
| Категория | Иллюстрации |
| Пункты | ГОСТ 7.32-2017 п. 6.5.8 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--error">error</span> |
| Объявлено в | `nk.rules.figures.figure_caption_hyphenation` |
| Фикстуры | `tests/fixtures/figure-caption-hyphenation/` |
| Автоисправление | да, ключом `--fix` |

Ищет в наименовании рисунка заданную вручную точку переноса `\-`.

## Почему это нарушение

Перенос слов в наименовании графического материала не допускается.

## Как исправить

Убрать `\-`. Длинное наименование сокращают либо переносят по границе слова.

## Нарушение

```latex
\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема экспе\-риментальной установки}
  \label{fig:setup}
\end{figure}
```

## Как правильно

```latex
\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

Наименование в несколько строк переносом слова не является.

\begin{figure}
  \includegraphics{img/plot.png}
  \caption{Зависимость погрешности измерений \\ от числа повторных запусков}
  \label{fig:plot}
\end{figure}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["figure-caption-hyphenation"]

[rules."figure-caption-hyphenation"]
severity = "info"
```
