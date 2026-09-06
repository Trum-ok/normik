"""Машинный вывод.

Стабильный контракт: изменение схемы — отдельное осознанное решение,
поэтому версия схемы вынесена в поле ``schema_version``.

1.1 — добавлено поле ``suppressed`` со счётчиками скрытых находок.
1.2 — у находки появился признак ``fixable``, в сводке — их число.
1.3 — у находки появился ``source``: чей это пункт. Стандарт задаёт профиль,
поэтому одно и то же правило под разными профилями даёт разные пункты.
1.4 — добавлен ``excerpt_offset``: длинную строку сокращают окном вокруг места
нарушения, и ``col`` считается по исходной строке, а не по показанной.
"""

import json
from typing import Any

from nk.core.finding import Finding
from nk.core.runner import RunResult

SCHEMA_VERSION = "1.4"
TOOL_NAME = "nk"


def render(result: RunResult) -> str:
    from nk import __version__

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": TOOL_NAME, "version": __version__},
        "profile": result.profile,
        "summary": {
            **{level.value: count for level, count in result.summary.items()},
            "files_checked": result.files_checked,
            "fixable": result.fixable,
        },
        "suppressed": {
            "inline": result.suppressed.inline,
            "baseline": result.suppressed.baseline,
        },
        "findings": [_finding(finding) for finding in result.findings],
        "failed_rules": [
            {"rule_id": failed.rule_id, "error": failed.error} for failed in result.failed_rules
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _finding(finding: Finding) -> dict[str, Any]:
    return {
        "rule_id": finding.rule_id,
        "clause": finding.clause,
        "source": finding.source,
        "severity": finding.severity.value,
        "message": finding.message,
        "requirement": finding.requirement,
        "path": str(finding.path),
        "lineno": finding.lineno,
        "col": finding.col,
        "excerpt": finding.excerpt,
        "excerpt_offset": finding.excerpt_offset,
        "context": list(finding.context),
        "suggestion": finding.suggestion,
        "fixable": finding.fix is not None,
    }
