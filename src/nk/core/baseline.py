"""Снимок известных нарушений.

Линтер, включённый на готовой работе, выдаёт сотни находок сразу. Снимок фиксирует
текущее состояние, и дальше показываются только новые нарушения: работа чинится
постепенно, а не «когда-нибудь потом».

Находка опознаётся не номером строки, а содержимым строки нарушения: отчёт растёт
весь семестр, и вставка абзаца выше не должна воскрешать все находки ниже. Если же
саму строку правили — находка всплывёт снова, и это правильно.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from nk.core.finding import Finding

SCHEMA_VERSION = "1.0"
TOOL_NAME = "nk"
FINGERPRINT_LENGTH = 16

#: Путь, ключ и отпечаток строки нарушения.
Key = tuple[str, str, str]


class BaselineError(ValueError):
    """Снимок не читается или испорчен."""


@dataclass(frozen=True, slots=True)
class Baseline:
    counts: dict[Key, int] = field(default_factory=dict)

    @classmethod
    def of(cls, findings: tuple[Finding, ...]) -> "Baseline":
        return cls(dict(Counter(fingerprint(finding) for finding in findings)))

    @classmethod
    def load(cls, path: Path) -> "Baseline":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise BaselineError(f"не удалось прочитать снимок {path}: {error}") from error
        except json.JSONDecodeError as error:
            raise BaselineError(f"снимок {path} испорчен: {error}") from error

        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise BaselineError(
                f"снимок {path} версии {version!r}, поддерживается {SCHEMA_VERSION!r}"
            )
        try:
            counts = {
                (entry["path"], entry["rule_id"], entry["fingerprint"]): int(entry["count"])
                for entry in data["entries"]
            }
        except (KeyError, TypeError, ValueError) as error:
            raise BaselineError(f"снимок {path}: неожиданная структура записи ({error})") from error
        return cls(counts)

    def dumps(self, version: str) -> str:
        entries = [
            {"path": path, "rule_id": rule_id, "fingerprint": digest, "count": count}
            for (path, rule_id, digest), count in sorted(self.counts.items())
        ]
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "tool": {"name": TOOL_NAME, "version": version},
            "entries": entries,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    def filter(self, findings: tuple[Finding, ...]) -> tuple[tuple[Finding, ...], int]:
        """Отсеять находки, уже учтённые снимком."""
        remaining = dict(self.counts)
        kept: list[Finding] = []
        for finding in findings:
            key = fingerprint(finding)
            available = remaining.get(key, 0)
            if available:
                remaining[key] = available - 1
                continue
            kept.append(finding)
        return tuple(kept), len(findings) - len(kept)


def fingerprint(finding: Finding) -> Key:
    """Ключ находки, устойчивый к сдвигу строк."""
    excerpt = " ".join((finding.excerpt or "").split())
    digest = sha256(excerpt.encode("utf-8")).hexdigest()[:FINGERPRINT_LENGTH]
    return (str(finding.path), finding.rule_id, digest)
