"""Запуск набора правил над документом и сбор находок.

Исключение внутри одного правила не роняет запуск: правило помечается как упавшее,
его находки отбрасываются, остальные правила отрабатывают. В публичном репозитории,
куда правила пишут разные люди, это условие работоспособности.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import RuleImpl


@dataclass(frozen=True, slots=True)
class FailedRule:
    rule_id: str
    error: str


@dataclass(frozen=True, slots=True)
class RunResult:
    profile: str
    findings: tuple[Finding, ...]
    failed_rules: tuple[FailedRule, ...] = ()
    files_checked: int = 0

    def __post_init__(self) -> None:
        # Порядок находок детерминирован во всех форматах, поэтому инвариант
        # держит сам результат, а не каждый форматтер по отдельности.
        object.__setattr__(
            self, "findings", tuple(sorted(self.findings, key=lambda item: item.sort_key))
        )
        object.__setattr__(
            self, "failed_rules", tuple(sorted(self.failed_rules, key=lambda item: item.rule_id))
        )

    @property
    def summary(self) -> dict[Severity, int]:
        counts = dict.fromkeys(Severity, 0)
        for finding in self.findings:
            counts[finding.severity] += 1
        return counts

    @property
    def has_errors(self) -> bool:
        return any(finding.severity is Severity.ERROR for finding in self.findings)


def run(
    document: Document,
    rules: Sequence[RuleImpl],
    *,
    extra_findings: Iterable[Finding] = (),
    threshold: Severity = Severity.INFO,
) -> RunResult:
    """Прогнать правила и собрать находки в детерминированном порядке."""
    findings: list[Finding] = list(extra_findings)
    failed: list[FailedRule] = []

    for impl in rules:
        try:
            produced = list(impl(document))
        except Exception as error:
            failed.append(FailedRule(rule_id=impl.id, error=f"{type(error).__name__}: {error}"))
            continue
        findings.extend(produced)

    return RunResult(
        profile=document.profile.name,
        findings=tuple(f for f in findings if f.severity.at_least(threshold)),
        failed_rules=tuple(failed),
        files_checked=len(document.files),
    )
