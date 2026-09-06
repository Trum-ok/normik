from pathlib import Path

import pytest

from nk.core.baseline import Baseline, BaselineError, fingerprint
from nk.core.finding import Finding, Severity

REPORT = Path("report.tex")


def make_finding(
    rule_id: str = "figure-caption-dot",
    lineno: int = 10,
    excerpt: str = "  \\caption{Схема установки.}",
    path: Path = REPORT,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        clause="6.5.7",
        severity=Severity.ERROR,
        message="сообщение",
        requirement="требование",
        path=path,
        lineno=lineno,
        excerpt=excerpt,
    )


def test_fingerprint_ignores_line_number() -> None:
    assert fingerprint(make_finding(lineno=10)) == fingerprint(make_finding(lineno=400))


def test_fingerprint_ignores_reindentation() -> None:
    left = make_finding(excerpt="  \\caption{Схема установки.}")
    right = make_finding(excerpt="\t\\caption{Схема  установки.}")
    assert fingerprint(left) == fingerprint(right)


def test_fingerprint_separates_rules_and_files() -> None:
    assert fingerprint(make_finding()) != fingerprint(make_finding(rule_id="G732-другое"))
    assert fingerprint(make_finding()) != fingerprint(make_finding(path=Path("другой.tex")))


def test_fingerprint_changes_with_the_line_content() -> None:
    assert fingerprint(make_finding()) != fingerprint(make_finding(excerpt="\\caption{Другое.}"))


def test_known_findings_are_filtered_out() -> None:
    findings = (make_finding(), make_finding(rule_id="G732-другое"))
    baseline = Baseline.of(findings)

    kept, hidden = baseline.filter(findings)

    assert kept == ()
    assert hidden == 2


def test_new_finding_survives_the_filter() -> None:
    baseline = Baseline.of((make_finding(),))

    kept, hidden = baseline.filter((make_finding(), make_finding(excerpt="\\caption{Новое.}")))

    assert [f.excerpt for f in kept] == ["\\caption{Новое.}"]
    assert hidden == 1


def test_repeated_violation_beyond_the_recorded_count_surfaces() -> None:
    baseline = Baseline.of((make_finding(lineno=1),))

    kept, hidden = baseline.filter((make_finding(lineno=1), make_finding(lineno=50)))

    assert len(kept) == 1
    assert hidden == 1


def test_roundtrip_through_json(tmp_path: Path) -> None:
    original = Baseline.of((make_finding(), make_finding(lineno=20)))
    path = tmp_path / ".nk-baseline.json"
    path.write_text(original.dumps("0.1.0"), encoding="utf-8")

    assert Baseline.load(path).counts == original.counts


def test_dump_is_deterministic() -> None:
    findings = (make_finding(rule_id="G732-б"), make_finding(rule_id="G732-а"))
    assert Baseline.of(findings).dumps("0.1.0") == Baseline.of(findings[::-1]).dumps("0.1.0")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(BaselineError, match="не удалось прочитать"):
        Baseline.load(tmp_path / "нет.json")


def test_broken_json(tmp_path: Path) -> None:
    path = tmp_path / "битый.json"
    path.write_text("{не json", encoding="utf-8")

    with pytest.raises(BaselineError, match="испорчен"):
        Baseline.load(path)


def test_foreign_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "будущий.json"
    path.write_text('{"schema_version": "9.0", "entries": []}', encoding="utf-8")

    with pytest.raises(BaselineError, match="версии"):
        Baseline.load(path)


def test_unexpected_entry_structure(tmp_path: Path) -> None:
    path = tmp_path / "кривой.json"
    path.write_text('{"schema_version": "1.0", "entries": [{"path": "a.tex"}]}', encoding="utf-8")

    with pytest.raises(BaselineError, match="структура"):
        Baseline.load(path)
