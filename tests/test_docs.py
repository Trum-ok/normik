from pathlib import Path

from nk.core.registry import load_rules
from nk.report import rules_docs

RULES_MD = Path(__file__).parent.parent / "docs" / "RULES.md"


def test_rules_docs_is_up_to_date() -> None:
    expected = rules_docs.render(load_rules())
    assert RULES_MD.read_text(encoding="utf-8") == expected, (
        "docs/RULES.md разошёлся с реестром — перегенерируйте: uv run nk rules docs"
    )


def test_every_rule_appears_in_the_docs() -> None:
    text = RULES_MD.read_text(encoding="utf-8")
    missing = [impl.id for impl in load_rules() if f"### {impl.id}" not in text]
    assert missing == [], f"правила без раздела в docs/RULES.md: {missing}"


def test_clauses_are_sorted_numerically() -> None:
    assert rules_docs._clause_key("6.10") > rules_docs._clause_key("6.9")
    assert rules_docs._clause_key("6.2.1") > rules_docs._clause_key("6.2")
