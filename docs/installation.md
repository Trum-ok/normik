# Установка

## Как инструмент

```bash
uv tool install normik
```

После этого команда `nk` доступна в системе:

```bash
nk --version
```

## Разовый запуск

```bash
uvx --from normik nk check chapters
```

## В окружение отчёта

Поставить рядом с остальными зависимостями работы:

```bash
uv pip install normik
```

## Из репозитория

Для работы над самим линтером:

```bash
git clone https://github.com/Trum-ok/normik.git
cd normik
uv sync
```

Внутри клона команда запускается через `uv run`:

```bash
uv run nk --version
```

## Требования

Python {{ python_requires }} или новее. Внешних зависимостей, кроме `typer` и `rich`, нет:
TeX-дистрибутив для работы `nk` не нужен — читаются исходники, а не собранный
документ.
