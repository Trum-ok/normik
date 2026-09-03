import pytest
from support import collect_rule_fixtures, make_document

from nk.core.document import Document
from nk.core.rule import RuleRegistry


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Параметризовать единый тест правил каталогами из ``tests/fixtures/``."""
    if "rule_fixture" not in metafunc.fixturenames:
        return
    fixtures = collect_rule_fixtures()
    metafunc.parametrize("rule_fixture", fixtures, ids=[item.rule.id for item in fixtures])


@pytest.fixture
def registry() -> RuleRegistry:
    """Пустой реестр, изолированный от глобального."""
    return RuleRegistry()


@pytest.fixture
def document() -> Document:
    return make_document(
        "\\begin{figure}[h]\n"
        "  \\includegraphics{img/setup.png}\n"
        "  \\caption{Схема экспериментальной установки.}\n"
        "\\end{figure}\n"
        "Текст после рисунка.\n"
    )
