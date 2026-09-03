from support import BAD, GOOD, RuleFixture, fixture_directories

from nk.core.registry import load_rules
from nk.parse.tex import parse


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
