# formula-no-reference

**Формула пронумерована, но ссылки на неё нет.**

| | |
|---|---|
| Категория | Формулы |
| Пункты | ГОСТ 7.32-2017 п. 6.8.3 |
| Уровень по умолчанию | `warning` |
| Объявлено в | `nk.rules.formulas.formula_reference` |
| Фикстуры | `tests/fixtures/formula-no-reference/` |
| Автоисправление | нет |

Ищет формулы в нумерующих окружениях, на которые в тексте нет ссылки.

## Почему это нарушение

Порядковый номер присваивают формулам, на которые в тексте есть ссылки.
Нумерация всех подряд формул сдвигает номера тех, на которые ссылаются.

## Как исправить

Сослаться на формулу либо снять с неё нумерацию — использовать вариант
окружения со звёздочкой.

## Нарушение

```latex
Расчёт погрешности приведён ниже.

\begin{equation}
  \delta = \frac{\Delta}{x} \cdot 100
  \label{eq:delta}
\end{equation}

Итоговое значение получено следующим образом.

\begin{gather}
  y = kx + b
\end{gather}
```

## Как правильно

```latex
Расчёт погрешности выполняется по формуле~\eqref{eq:delta}.

\begin{equation}
  \delta = \frac{\Delta}{x} \cdot 100
  \label{eq:delta}
\end{equation}

Промежуточное преобразование нумерации не требует.

\begin{equation*}
  y = kx + b
\end{equation*}

\begin{displaymath}
  z = y^2
\end{displaymath}
```

## Настройка

Отключить правило либо изменить его уровень [профилем](../profiles.md):

```toml
disable = ["formula-no-reference"]

[rules."formula-no-reference"]
severity = "info"
```
