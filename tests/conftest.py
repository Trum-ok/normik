"""Общие фикстуры тестов."""

from pathlib import Path

import pytest

from nk.core.document import Document, Line
from nk.core.profile import Profile
from nk.core.rule import RuleRegistry


@pytest.fixture
def registry() -> RuleRegistry:
    """Пустой реестр, изолированный от глобального."""
    return RuleRegistry()


def make_document(text: str, path: str = "report.tex", profile: Profile | None = None) -> Document:
    """Собрать документ из текста без участия парсера."""
    file_path = Path(path)
    lines = tuple(
        Line(path=file_path, lineno=number, raw=raw, stripped=raw)
        for number, raw in enumerate(text.splitlines(), start=1)
    )
    return Document(
        root=file_path,
        files=(file_path,),
        lines=lines,
        profile=profile or Profile(),
    )


@pytest.fixture
def document() -> Document:
    return make_document(
        "\\begin{figure}[h]\n"
        "  \\includegraphics{img/setup.png}\n"
        "  \\caption{Схема экспериментальной установки.}\n"
        "\\end{figure}\n"
        "Текст после рисунка.\n"
    )
