from support import BAD, GOOD, RuleFixture, fixture_directories

from nk.core.fixer import plan
from nk.core.registry import load_rules
from nk.parse.tex import parse

FIX_PASSES = 5


def findings_for(rule_fixture: RuleFixture, name: str) -> list:
    result = parse([rule_fixture.directory / name])
    assert result.issues == (), f"фикстура {name} не разбирается: {result.issues}"
    return list(rule_fixture.rule(result.document))


def test_bad_fixture_flags_exactly_the_marked_lines(rule_fixture: RuleFixture) -> None:
    expected = rule_fixture.expected_lines()
    assert expected, f"в {rule_fixture.bad} нет ни одной строки с пометкой % EXPECT"

    findings = findings_for(rule_fixture, BAD)
    assert findings, f"правило {rule_fixture.rule.id} не сработало на {BAD}"
    assert {finding.lineno for finding in findings} == expected


def test_good_fixture_gives_no_findings(rule_fixture: RuleFixture) -> None:
    findings = findings_for(rule_fixture, GOOD)
    assert findings == [], f"ложные срабатывания в {GOOD}: {[f.lineno for f in findings]}"


def test_findings_are_self_contained(rule_fixture: RuleFixture) -> None:
    for finding in findings_for(rule_fixture, BAD):
        where = f"{rule_fixture.rule.id}, строка {finding.lineno}"
        assert finding.message.strip(), f"{where}: пустое message"
        assert finding.requirement.strip(), f"{where}: пустое requirement"
        assert finding.context, f"{where}: пустой context"
        assert finding.clause == rule_fixture.rule.clause, (
            f"{where}: clause разошёлся с объявлением"
        )
        if not rule_fixture.rule.allow_missing_suggestion:
            assert finding.suggestion, (
                f"{where}: нет suggestion. Если исправление принципиально неоднозначно, "
                "объявите правило с allow_missing_suggestion=True"
            )


def test_every_fixture_directory_matches_a_rule() -> None:
    registry = load_rules()
    orphans = [path.name for path in fixture_directories() if path.name not in registry]
    assert orphans == [], f"фикстуры без правила: {orphans}"


def test_every_rule_has_fixtures() -> None:
    names = {path.name for path in fixture_directories()}
    missing = [impl.id for impl in load_rules() if impl.id not in names]
    assert missing == [], f"правила без каталога фикстур: {missing}"


def test_fixture_directories_are_complete() -> None:
    incomplete = [
        path.name
        for path in fixture_directories()
        if not (path / BAD).is_file() or not (path / GOOD).is_file()
    ]
    assert incomplete == [], f"в каталогах фикстур не хватает {BAD} или {GOOD}: {incomplete}"


def test_fixable_flag_matches_reality(rule_fixture: RuleFixture) -> None:
    findings = findings_for(rule_fixture, BAD)
    produces_fixes = any(finding.fix is not None for finding in findings)
    assert produces_fixes == rule_fixture.rule.fixable, (
        f"{rule_fixture.rule.id}: fixable={rule_fixture.rule.fixable}, "
        f"а правки {'есть' if produces_fixes else 'отсутствуют'}"
    )


def test_fixes_actually_remove_the_violation(rule_fixture: RuleFixture, tmp_path) -> None:
    """Применённая правка обязана убирать нарушение и не создавать новых.

    Правило может не давать правок вовсе либо давать их части находок —
    например номер формулы, вписанный цифрой, в скобки автоматически не берётся.
    """
    source = tmp_path / BAD
    source.write_text(rule_fixture.bad.read_text(encoding="utf-8"), encoding="utf-8")

    result = parse([source])
    findings = list(rule_fixture.rule(result.document))
    fixable = [finding for finding in findings if finding.fix is not None]
    if not fixable:
        return

    for _ in range(FIX_PASSES):
        parsed = parse([source])
        remaining = [f for f in rule_fixture.rule(parsed.document) if f.fix is not None]
        if not remaining:
            break
        applied = plan(remaining)
        assert applied.applied, f"правки {rule_fixture.rule.id} не применились"
        for edit in applied.edits:
            edit.path.write_text(edit.text, encoding="utf-8")

    left = list(rule_fixture.rule(parse([source]).document))
    assert [f for f in left if f.fix is not None] == [], (
        f"правки {rule_fixture.rule.id} не сходятся: после применения находка с правкой осталась"
    )
    assert len(left) <= len(findings) - len(fixable), (
        f"правки {rule_fixture.rule.id} породили новые нарушения"
    )
