# Интеграции

## GitHub Actions

Проверка исходников отчёта на каждый push и pull request:

```yaml
name: gost

on: [ push, pull_request ]

jobs:
  nk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10

      - name: nk check
        run: uvx --from normik nk check chapters
```

Сборка падает на находках уровня `error`. Чтобы падала и на предупреждениях,
поднимите им уровень в [профиле](profiles.md).

Если линтер включается на работе, где нарушений уже много, зафиксируйте их
[снимком](usage.md#снимок-известных-нарушений) и добавьте ключ — тогда сборка
падает только на новых:

```yaml
      - name: nk check
        run: >-
          uvx --from normik
          nk check chapters --baseline .nk-baseline.json
```

Машинный вывод для своих аннотаций:

```bash
nk check chapters --format json > findings.json
```

## Автоисправление перед коммитом

```bash
nk check chapters --fix
```

В CI ключ не нужен: сборка должна падать на нарушениях, а не переписывать
исходники за автора.

## Локальный хук

`.git/hooks/pre-commit`:

```bash
#!/bin/sh
uv run nk check chapters --quiet || {
  echo "nk: в исходниках есть нарушения, запустите: uv run nk check chapters"
  exit 1
}
```

## Передача агенту

Формат `agent` рассчитан на то, что вывод копируется в Claude Code целиком,
без пояснений: каждая находка содержит путь, строку, суть нарушения,
требование и готовое исправление.

```bash
nk check chapters --format agent
```

Число находок в выводе ограничено по умолчанию — длинный список вытесняет из
контекста агента сам отчёт. Разумный порядок работы: исправить показанное,
запустить снова. Снять предел — `--limit 0`.

Часть находок чинится автоматически — их применяет сам `nk` по ключу `--fix`.
Остальные остаются предложением текстом: замена в них неоднозначна, и что
именно применить, решает человек или агент.
