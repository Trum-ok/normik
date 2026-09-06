"""Запуск набора правил над документом и сбор находок.

Исключение внутри одного правила не роняет запуск: правило помечается как упавшее,
его находки отбрасываются, остальные правила отрабатывают. В публичном репозитории,
куда правила пишут разные люди, это условие работоспособности.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from nk.core import diagnostics
from nk.core.baseline import Baseline
from nk.core.diagnostics import IGNORE_UNKNOWN, IGNORE_UNUSED, INTERNAL
from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import RuleImpl
from nk.core.suppressions import Suppression, Suppressions


@dataclass(frozen=True, slots=True)
class FailedRule:
    rule_id: str
    error: str


@dataclass(frozen=True, slots=True)
class Suppressed:
    """Сколько находок скрыто и чем."""

    inline: int = 0
    baseline: int = 0

    @property
    def total(self) -> int:
        return self.inline + self.baseline


@dataclass(frozen=True, slots=True)
class RunResult:
    profile: str
    findings: tuple[Finding, ...]
    failed_rules: tuple[FailedRule, ...] = ()
    files_checked: int = 0
    suppressed: Suppressed = Suppressed()

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
    def fixable(self) -> int:
        """Сколько находок снимает ключ ``--fix``."""
        return sum(1 for finding in self.findings if finding.fix is not None)

    @property
    def has_errors(self) -> bool:
        return any(finding.severity is Severity.ERROR for finding in self.findings)


def run(
    document: Document,
    rules: Sequence[RuleImpl],
    *,
    extra_findings: Iterable[Finding] = (),
    threshold: Severity = Severity.INFO,
    suppressions: Suppressions | None = None,
    baseline: Baseline | None = None,
    ignored: frozenset[str] = frozenset(),
    known_ids: frozenset[str] | None = None,
) -> RunResult:
    """Прогнать правила и собрать находки в детерминированном порядке.

    ``suppressions`` — директивы из исходников, ``baseline`` — снимок уже известных
    нарушений. Порог по уровню применяется последним: подавления и снимок работают
    на полном наборе, иначе результат зависел бы от ключа ``--severity``.
    """
    findings: list[Finding] = list(extra_findings)
    failed: list[FailedRule] = []

    for impl in rules:
        try:
            produced = list(impl(document))
        except Exception as error:
            failed.append(FailedRule(rule_id=impl.id, error=f"{type(error).__name__}: {error}"))
            continue
        findings.extend(produced)

    ordered = sorted(
        (item for item in findings if item.rule_id not in ignored),
        key=lambda item: item.sort_key,
    )
    kept, inline = _apply_suppressions(ordered, suppressions)
    if suppressions is not None:
        kept.extend(_directive_diagnostics(document, suppressions, rules, ignored, known_ids))

    from_baseline = 0
    if baseline is not None:
        filtered, from_baseline = baseline.filter(tuple(kept))
        kept = list(filtered)

    return RunResult(
        profile=document.profile.name,
        findings=tuple(f for f in kept if f.severity.at_least(threshold)),
        failed_rules=tuple(failed),
        files_checked=len(document.files),
        suppressed=Suppressed(inline=inline, baseline=from_baseline),
    )


def _apply_suppressions(
    findings: list[Finding], suppressions: Suppressions | None
) -> tuple[list[Finding], int]:
    if suppressions is None:
        return list(findings), 0
    kept = [finding for finding in findings if suppressions.match(finding) is None]
    return kept, len(findings) - len(kept)


def _directive_diagnostics(
    document: Document,
    suppressions: Suppressions,
    rules: Sequence[RuleImpl],
    ignored: frozenset[str],
    known_ids: frozenset[str] | None,
) -> list[Finding]:
    """Директивы, ссылающиеся в никуда, и директивы, ставшие лишними."""
    findings: list[Finding] = []
    active = ({impl.id for impl in rules} | set(INTERNAL)) - ignored

    for item in suppressions.items:
        unknown = sorted(
            rule_id
            for rule_id in item.rule_ids
            if known_ids is not None and rule_id not in known_ids
        )
        if unknown:
            listed = ", ".join(unknown)
            findings.append(
                _diagnostic(
                    document,
                    item,
                    IGNORE_UNKNOWN,
                    message=f"Подавление ссылается на неизвестное правило: {listed}.",
                    requirement="Идентификаторы в директиве подавления должны существовать.",
                    suggestion="Сверить идентификатор с выводом nk rules list.",
                )
            )

    if IGNORE_UNUSED in ignored:
        return findings

    for item in suppressions.unused():
        # Правило, выключенное профилем или ключом, до находок не доходит;
        # жаловаться на подавление для него было бы шумом.
        if item.rule_ids and not (item.rule_ids & active):
            continue
        findings.append(
            _diagnostic(
                document,
                item,
                IGNORE_UNUSED,
                message="Подавление ничего не подавило.",
                requirement="Директивы подавления не должны переживать исправленное нарушение.",
                suggestion="Убрать директиву.",
            )
        )
    return findings


def _diagnostic(
    document: Document,
    item: Suppression,
    code: str,
    *,
    message: str,
    requirement: str,
    suggestion: str,
) -> Finding:
    return diagnostics.to_finding(
        code,
        message=message,
        requirement=requirement,
        path=item.path,
        lineno=item.lineno,
        suggestion=suggestion,
        excerpt=document.excerpt(item.path, item.lineno),
        context=document.context(item.path, item.lineno),
    )
