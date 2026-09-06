# figure-caption-position

**Наименование рисунка расположено выше изображения.**

| | |
|---|---|
| Категория | Иллюстрации |
| Источник требования | стандарт |
| Пункты | ГОСТ 7.32-2017 п. 6.5.7<br>ГОСТ Р 2.105-2019 п. 6.9.4 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--error">error</span> |
| Объявлено в | `nk.rules.figures.figure_caption_position` |
| Фикстуры | `tests/fixtures/figure-caption-position/` |
| Автоисправление | нет |

Сравнивает положение `\caption` с первой строкой, вставляющей изображение,
внутри окружения рисунка.

## Почему это нарушение

Слово «Рисунок», номер и наименование помещают под рисунком. Подпись сверху
читается как заголовок раздела и отрывается от иллюстрации при переносе на
другую страницу.

## Как исправить

Перенести `\caption` ниже команды вставки изображения, вместе с `\label`.

## Нарушение

```latex
\begin{figure}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
  \includegraphics{img/setup.png}
\end{figure}
```

## Как правильно

```latex
\begin{figure}
  \centering
  \includegraphics{img/setup.png}
  \caption{Схема экспериментальной установки}
  \label{fig:setup}
\end{figure}

Подпись таблицы стоит выше таблицы — это её штатное место.

\begin{table}
  \caption{Результаты измерений}
  \begin{tabular}{ll}
    а & б \\
  \end{tabular}
\end{table}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["figure-caption-position"]

[rules."figure-caption-position"]
severity = "info"
```
