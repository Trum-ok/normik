import pytest
from helpers import make_finding

from nk.core.finding import Severity
from nk.core.runner import FailedRule, RunResult


@pytest.fixture
def result() -> RunResult:
    return RunResult(
        profile="base",
        findings=(
            make_finding(),
            make_finding(
                "G732-6.6.2-table-no-reference",
                clause="6.6.2",
                severity=Severity.WARNING,
                lineno=160,
                col=None,
            ),
            make_finding(
                "G732-6.2.4-heading-hyphenation",
                clause="6.2.4",
                severity=Severity.INFO,
                path="chapters/01-intro.tex",
                lineno=12,
            ),
        ),
        failed_rules=(FailedRule(rule_id="G732-плохое", error="ValueError: сломалось"),),
        files_checked=12,
    )
