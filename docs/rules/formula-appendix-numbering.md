# formula-appendix-numbering

**Формула приложения нумеруется без обозначения приложения.**

| | |
|---|---|
| Категория | Формулы |
| Пункты | ГОСТ 7.32-2017 п. 6.8.5 |
| Уровень по умолчанию | `error` |
| Объявлено в | `nk.rules.formulas.appendix_formula_numbering` |
| Фикстуры | `tests/fixtures/formula-appendix-numbering/` |
| Автоисправление | нет |

Проверяет, что формулы внутри приложения нумеруются с его обозначением.

## Почему это нарушение

Нумерация в приложении отдельная: она начинается заново и несёт обозначение
самого приложения. Сквозной номер из основной части ссылку «формула А.1»
сделать не позволяет.

## Как исправить

Задать схему нумерации в пределах раздела — тогда внутри приложения номер
складывается из его буквы и порядкового номера.

## Нарушение

```latex
\section{Методика}

\begin{equation}
  \delta = \frac{\Delta}{x}
\end{equation}

\section*{ПРИЛОЖЕНИЕ В}

\begin{equation}
  y = kx + b
\end{equation}
```

## Как правильно

```latex
\numberwithin{equation}{section}

\section{Методика}

\begin{equation}
  \delta = \frac{\Delta}{x}
\end{equation}

\section*{ПРИЛОЖЕНИЕ В}

\begin{equation}
  y = kx + b
\end{equation}

Ненумерованная формула в приложении обозначения не требует.

\begin{equation*}
  z = y^2
\end{equation*}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["formula-appendix-numbering"]

[rules."formula-appendix-numbering"]
severity = "info"
```
