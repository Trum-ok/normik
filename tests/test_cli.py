import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nk.cli import EXIT_FOUND_ERRORS, EXIT_INTERNAL_ERROR, EXIT_OK, app

RULE_ID = "G732-6.5.7-caption-dot"

runner = CliRunner()


@pytest.fixture
def report(tmp_path: Path) -> Path:
    path = tmp_path / "report.tex"
    path.write_text(
        "\\begin{figure}\n  \\caption{Схема установки.}\n\\end{figure}\n", encoding="utf-8"
    )
    return path


@pytest.fixture
def clean_report(tmp_path: Path) -> Path:
    path = tmp_path / "clean.tex"
    path.write_text(
        "\\begin{figure}\n  \\caption{Схема установки}\n\\end{figure}\n", encoding="utf-8"
    )
    return path


def test_clean_report_exits_zero(clean_report: Path) -> None:
    assert runner.invoke(app, ["check", str(clean_report)]).exit_code == EXIT_OK


def test_error_finding_exits_one(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--format", "agent"])

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert RULE_ID in result.stdout
    assert "Исправить: \\caption{Схема установки}" in result.stdout


def test_quiet_prints_nothing(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--quiet"])

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert result.stdout == ""


def test_ignore_switches_off_the_rule(report: Path) -> None:
    assert runner.invoke(app, ["check", str(report), "--ignore", RULE_ID]).exit_code == EXIT_OK


def test_select_narrows_to_one_rule(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--select", RULE_ID])
    assert result.exit_code == EXIT_FOUND_ERRORS


def test_missing_path_exits_two() -> None:
    assert runner.invoke(app, ["check", "нет-такого-файла.tex"]).exit_code == EXIT_INTERNAL_ERROR


def test_unknown_rule_in_select_exits_two(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--select", "G732-нет"])

    assert result.exit_code == EXIT_INTERNAL_ERROR
    assert "неизвестное правило 'G732-нет'" in result.output


def test_unknown_profile_exits_two(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--profile", "нет-профиля"])
    assert result.exit_code == EXIT_INTERNAL_ERROR


def test_profile_disables_the_rule(tmp_path: Path, report: Path) -> None:
    profile = tmp_path / "кафедра.toml"
    profile.write_text(f'name = "Кафедра N"\nextends = "base"\ndisable = ["{RULE_ID}"]\n', "utf-8")

    result = runner.invoke(app, ["check", str(report), "--profile", str(profile)])
    assert result.exit_code == EXIT_OK


def test_profile_lowers_severity(tmp_path: Path, report: Path) -> None:
    profile = tmp_path / "кафедра.toml"
    profile.write_text(f'[rules."{RULE_ID}"]\nseverity = "warning"\n', "utf-8")

    result = runner.invoke(app, ["check", str(report), "--profile", str(profile), "-f", "agent"])

    assert result.exit_code == EXIT_OK
    assert f"  warning  {RULE_ID}" in result.stdout


def test_json_output_is_parseable(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--format", "json"])

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0"
    assert payload["summary"]["error"] == 1
    assert payload["findings"][0]["rule_id"] == RULE_ID
    assert payload["findings"][0]["clause"] == "6.5.7"


def test_rules_list_shows_the_rule() -> None:
    result = runner.invoke(app, ["rules", "list"])

    assert result.exit_code == EXIT_OK
    assert RULE_ID in result.stdout


def test_rules_show_reports_the_declaration() -> None:
    result = runner.invoke(app, ["rules", "show", RULE_ID])

    assert result.exit_code == EXIT_OK
    assert "6.5.7" in result.stdout
    assert "nk.rules.elements.figure_caption_dot" in result.stdout


def test_profile_show_lists_the_active_set() -> None:
    result = runner.invoke(app, ["profile", "show"])

    assert result.exit_code == EXIT_OK
    assert "Профиль: base" in result.stdout
    assert RULE_ID in result.stdout
