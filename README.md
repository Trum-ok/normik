# normik

[![ci](https://github.com/Trum-ok/normik/actions/workflows/ci.yaml/badge.svg)](https://github.com/Trum-ok/normik/actions/workflows/ci.yaml)
[![pypi](https://img.shields.io/pypi/v/normik)](https://pypi.org/project/normik/)
[![python](https://img.shields.io/pypi/pyversions/normik)](https://pypi.org/project/normik/)
[![license](https://img.shields.io/github/license/Trum-ok/normik)](https://github.com/Trum-ok/normik/blob/master/LICENSE)

`nk` — линтер оформления отчётных документов по ГОСТ для исходников LaTeX.

**Документация: <https://trum-ok.github.io/normik/>**

Принимает `.tex` и выдаёт список нарушений с указанием пункта стандарта, файла
и строки. Стандарт задаётся профилем — перечень поддержанных на странице
[Профили](https://trum-ok.github.io/normik/profiles/#стандарт-и-свой-источник-требований).

```bash
nk check report.tex
```

```text
report.tex
  1:17  warning  figure-reference-word  (ГОСТ 7.32-2017 п. 6.5.1)
    Нарушение: В ссылке на иллюстрацию использовано сокращение «рис.».
    Требуется: При ссылке пишут слово «рисунок» полностью и его номер.
    Исправить: Заменить «рис.» на «рисунок» в нужном падеже.
    > 1 | Как показано на рис.~\ref{fig:speed}, зависимость линейная.
        |                 ^
      2 | 
      3 | \begin{figure}[h]

  5:5  error  figure-caption-dot  (ГОСТ 7.32-2017 п. 6.5.7)
    Нарушение: Наименование рисунка заканчивается точкой.
    Требуется: Наименование рисунка приводят с прописной буквы без точки в конце.
    Исправить: \caption{Зависимость скорости от нагрузки}
      3 | \begin{figure}[h]
      4 |     \includegraphics{plot.png}
    > 5 |     \caption{Зависимость скорости от нагрузки.}
      6 |     \label{fig:speed}
      7 | \end{figure}

Итого: 1 error, 1 warning, 0 info.
Исправимо ключом --fix: 1
Другие форматы: --format json | agent
```

## Установка

```bash
uv tool install normik
```

После этого команда `nk` доступна в системе. Разовый запуск без установки:

```bash
uvx --from normik nk check chapters
```

## Примеры запуска

Проверить весь каталог с исходниками:

```bash
nk check chapters
```

Получить вывод, который можно скопировать в Claude Code без пояснений:

```bash
nk check chapters --format agent
```

Проверить по профилю кафедры, показывая только ошибки:

```bash
nk check report.tex --profile profiles/example-university.toml --severity error
```

Без ключа профиль ищется рядом с исходниками — `nk.toml`, `.nk.toml` или секция
`[tool.nk]` в `pyproject.toml`.

Починить то, что чинится механически — сначала посмотреть, потом применить:

```bash
nk check chapters --diff
nk check chapters --fix
```

Включить линтер на готовой работе: зафиксировать текущие нарушения снимком
и дальше видеть только новые:

```bash
nk check chapters --write-baseline .nk-baseline.json
nk check chapters --baseline .nk-baseline.json
```

## Команды

| Команда                 | Назначение                                     |
|-------------------------|------------------------------------------------|
| `nk check PATH...`      | проверить исходники                            |
| `nk rules list`         | перечень правил                                |
| `nk rules show RULE_ID` | подробности по правилу                         |
| `nk profile show`       | итоговый набор правил после применения профиля |

Разработка и добавление правил — [CONTRIBUTING.md](CONTRIBUTING.md).
