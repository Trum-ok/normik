# normik

[![ci](https://github.com/Trum-ok/normik/actions/workflows/ci.yaml/badge.svg)](https://github.com/Trum-ok/normik/actions/workflows/ci.yaml)

`nk` — линтер оформления отчёта о НИР по ГОСТ 7.32-2017 для исходников LaTeX.

**Документация: <https://trum-ok.github.io/normik/>**

Принимает `.tex` и выдаёт список нарушений с указанием пункта стандарта, файла
и строки. Инструмент детерминированный: одни и те же входные данные всегда дают
один и тот же вывод. LLM внутри не используется.

Проверяются только исходники. Требования, проверяемые по скомпилированному
документу — поля, гарнитуры, кегль, колонцифры, — в область видимости не входят.

## Установка

```bash
uv sync
```

## Примеры запуска

Проверить весь каталог с исходниками:

```bash
uv run nk check chapters
```

Получить вывод, который можно скопировать в Claude Code без пояснений:

```bash
uv run nk check chapters --format agent
```

Проверить по профилю кафедры, показывая только ошибки:

```bash
uv run nk check report.tex --profile profiles/example-university.toml --severity error
```

Включить линтер на готовой работе: зафиксировать текущие нарушения снимком
и дальше видеть только новые:

```bash
uv run nk check chapters --write-baseline .nk-baseline.json
uv run nk check chapters --baseline .nk-baseline.json
```

## Команды

| Команда | Назначение |
|---|---|
| `nk check PATH...` | проверить исходники |
| `nk rules list` | перечень правил |
| `nk rules show RULE_ID` | подробности по правилу |
| `nk rules docs` | пересобрать страницы правил в `docs/rules/` |
| `nk profile show` | итоговый набор правил после применения профиля |

Ключи `check`, коды возврата и форматы вывода — на странице
[Использование](https://trum-ok.github.io/normik/usage/).

## Документация

| Страница | О чём |
|---|---|
| [Использование](https://trum-ok.github.io/normik/usage/) | команды, ключи, форматы вывода, коды возврата, подавления, снимок |
| [Профили](https://trum-ok.github.io/normik/profiles/) | подстройка набора правил под кафедру |
| [Правила](https://trum-ok.github.io/normik/rules/) | страница на каждое правило: почему, пример, настройка |
| [Интеграции](https://trum-ok.github.io/normik/integrations/) | CI, хук, передача вывода агенту |
| [Как добавить правило](https://trum-ok.github.io/normik/contributing/) | руководство для соавторов |

Исходники документации — в каталоге [`docs/`](docs); каталог
[`docs/rules/`](docs/rules) генерируется командой `uv run nk rules docs`
и руками не редактируется.

## Разработка

```bash
make check      # ruff, ty, pytest
make docs       # перегенерировать правила и собрать сайт
make docs-serve # локальный просмотр на http://127.0.0.1:8000
```
