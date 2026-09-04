# Установка

## Из репозитория

```bash
git clone https://github.com/Trum-ok/normik.git
cd normik
uv sync
```

Дальше `nk` запускается через `uv run`:

```bash
uv run nk --version
```

## Как инструмент проекта

Поставить в окружение отчёта прямо из репозитория:

```bash
uv pip install git+https://github.com/Trum-ok/normik.git
```

После этого команда доступна как `nk`.

## Разовый запуск

```bash
uvx --from git+https://github.com/Trum-ok/normik.git nk check chapters
```

## Требования

Python 3.13.4 или новее. Внешних зависимостей, кроме `typer` и `rich`, нет:
TeX-дистрибутив для работы `nk` не нужен — читаются исходники, а не собранный
документ.
