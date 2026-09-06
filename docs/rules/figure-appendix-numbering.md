# figure-appendix-numbering

**Иллюстрация приложения нумеруется без его обозначения.**

| | |
|---|---|
| Категория | Иллюстрации |
| Пункты | ГОСТ 7.32-2017 п. 6.5.5<br>ГОСТ Р 2.105-2019 п. 6.9.3 |
| Уровень по умолчанию | <span class="nk-severity nk-severity--error">error</span> |
| Объявлено в | `nk.rules.figures.appendix_figure_numbering` |
| Фикстуры | `tests/fixtures/figure-appendix-numbering/` |
| Автоисправление | нет |

Проверяет, что иллюстрации внутри приложения нумеруются с его обозначением.

## Почему это нарушение

Нумерация в приложении отдельная: она начинается заново и несёт обозначение
самого приложения. Сквозной номер из основной части ссылку «рисунок А.1»
сделать не позволяет.

## Как исправить

Задать схему нумерации в пределах раздела — тогда внутри приложения номер
складывается из его буквы и порядкового номера.

## Нарушение

```latex
\section{Методика}

\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема установки}
\end{figure}

\section*{ПРИЛОЖЕНИЕ А}

\begin{figure}
  \includegraphics{img/scheme.png}
  \caption{Общий вид стенда}
\end{figure}
```

## Как правильно

```latex
\counterwithin{figure}{section}

\section{Методика}

\begin{figure}
  \includegraphics{img/setup.png}
  \caption{Схема установки}
\end{figure}

\section*{ПРИЛОЖЕНИЕ А}

\begin{figure}
  \includegraphics{img/scheme.png}
  \caption{Общий вид стенда}
\end{figure}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["figure-appendix-numbering"]

[rules."figure-appendix-numbering"]
severity = "info"
```
