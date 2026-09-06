# Участие в разработке

## Окружение

```bash
git clone https://github.com/Trum-ok/normik.git
cd normik
uv sync
```

Внутри клона команда запускается через `uv run`:

```bash
uv run nk check chapters
```

## Проверки

```bash
make check      # ruff, ty, pytest
make lint       # только линтеры и проверка типов
make test       # только тесты
make format     # автоформатирование
make coverage   # покрытие: сводка в терминал, подробности в htmlcov/index.html
```

## Документация

Исходники сайта — в каталоге
[`docs/`](https://github.com/Trum-ok/normik/tree/master/docs). Каталог
[`docs/rules/`](https://github.com/Trum-ok/normik/tree/master/docs/rules)
генерируется командой `uv run nk rules docs` и руками не редактируется.

```bash
make docs       # перегенерировать правила и собрать сайт
make docs-serve # локальный просмотр на http://127.0.0.1:8000
```

## Новое правило

Правило — это один файл в `src/nk/rules/` и один каталог в `tests/fixtures/`.
Рецепт, полный пример, требования к тексту находки и правка для `--fix` —
в руководстве [Как добавить правило](https://trum-ok.github.io/normik/contributing/).
