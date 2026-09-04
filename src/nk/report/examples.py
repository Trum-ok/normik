"""Примеры к правилам, взятые из тестовых фикстур.

Пример в документации — тот же файл, на котором правило проверяется тестом, поэтому
разойтись с поведением линтера он не может. Фикстуры лежат вне пакета, и при установке
из колеса их нет: тогда пример просто не показывается.
"""

from dataclasses import dataclass
from pathlib import Path

DEFAULT_FIXTURES_ROOT = Path("tests/fixtures")

BAD_FILE = "bad.tex"
GOOD_FILE = "good.tex"

EXPECT_MARKER = "% EXPECT"
DOC_BEGIN = "% DOC-BEGIN"
DOC_END = "% DOC-END"


@dataclass(frozen=True, slots=True)
class Example:
    """Пара фрагментов: с нарушением и без него."""

    bad: str
    good: str


def load(rule_id: str, root: Path | None = None) -> Example | None:
    """Прочитать фикстуры правила. ``None`` — если каталога нет."""
    directory = (root or DEFAULT_FIXTURES_ROOT) / rule_id
    bad = _fragment(directory / BAD_FILE)
    good = _fragment(directory / GOOD_FILE)
    if bad is None or good is None:
        return None
    return Example(bad=bad, good=good)


def _fragment(path: Path) -> str | None:
    """Фрагмент для показа: между метками ``DOC-BEGIN``/``DOC-END`` либо файл целиком."""
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(_strip_markers(_between_markers(lines))) or None


def _between_markers(lines: list[str]) -> list[str]:
    begin = _index_of(lines, DOC_BEGIN)
    end = _index_of(lines, DOC_END)
    if begin is None or end is None or end <= begin:
        return lines
    return lines[begin + 1 : end]


def _index_of(lines: list[str], marker: str) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == marker:
            return index
    return None


def _strip_markers(lines: list[str]) -> list[str]:
    # % EXPECT адресован тесту: в примере он только сбивает читающего.
    cleaned = [line.split(EXPECT_MARKER)[0].rstrip() for line in lines]
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return cleaned
