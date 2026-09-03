"""Общее для тестов: сборка документа и автосбор фикстур правил.

Каталог ``tests/fixtures/<rule_id>/`` с файлами ``bad.tex`` и ``good.tex``
сопоставляется с реестром и параметризует единый тест из ``test_rules.py``.
Автору правила писать тестовый код не нужно.
"""

from dataclasses import dataclass
from pathlib import Path

from nk.core.document import Document, Line
from nk.core.profile import Profile
from nk.core.registry import load_rules
from nk.core.rule import RuleImpl

FIXTURES = Path(__file__).parent / "fixtures"

#: Комментарий, которым в ``bad.tex`` помечают строки, где правило обязано сработать.
EXPECT_MARKER = "% EXPECT"

BAD = "bad.tex"
GOOD = "good.tex"


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


@dataclass(frozen=True, slots=True)
class RuleFixture:
    rule: RuleImpl
    directory: Path

    @property
    def bad(self) -> Path:
        return self.directory / BAD

    @property
    def good(self) -> Path:
        return self.directory / GOOD

    def expected_lines(self) -> set[int]:
        """Строки ``bad.tex``, помеченные ``% EXPECT``."""
        text = self.bad.read_text(encoding="utf-8")
        return {
            lineno
            for lineno, line in enumerate(text.splitlines(), start=1)
            if EXPECT_MARKER in line
        }


def fixture_directories() -> list[Path]:
    if not FIXTURES.is_dir():
        return []
    return sorted(
        path for path in FIXTURES.iterdir() if path.is_dir() and not path.name.startswith("_")
    )


def collect_rule_fixtures() -> list[RuleFixture]:
    registry = load_rules()
    return [
        RuleFixture(rule=registry.get(path.name), directory=path)
        for path in fixture_directories()
        if path.name in registry
    ]
