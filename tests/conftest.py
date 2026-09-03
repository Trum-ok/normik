import pytest
from support import make_document

from nk.core.document import Document
from nk.core.rule import RuleRegistry


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
