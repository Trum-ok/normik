from collections.abc import Iterable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nk.cli import EXIT_FOUND_ERRORS, EXIT_INTERNAL_ERROR, EXIT_OK, app
from nk.core.document import Document
from nk.core.finding import Finding, Severity
from nk.core.rule import REGISTRY, rule

runner = CliRunner()


@pytest.fixture
def caption_dot_rule():
    """Зарегистрировать правило в глобальном реестре на время теста."""

    @rule(
        id="G732-6.5.7-caption-dot",
        clause="6.5.7",
        severity=Severity.ERROR,
        title="Подпись рисунка заканчивается точкой",
    )
    def caption_dot(doc: Document) -> Iterable[Finding]:
        for line in doc.iter_lines():
            if "\\caption{" in line.stripped and line.stripped.rstrip().endswith(".}"):
                yield caption_dot.finding(
                    doc,
                    line,
                    message="Подпись рисунка заканчивается точкой.",
                    requirement="Наименование рисунка приводят без точки в конце.",
                    suggestion="Убрать точку в конце подписи.",
                )

    yield caption_dot
    REGISTRY.clear()


@pytest.fixture
def report(tmp_path: Path) -> Path:
    path = tmp_path / "report.tex"
    path.write_text(
        "\\begin{figure}\n  \\caption{Схема установки.}\n\\end{figure}\n", encoding="utf-8"
    )
    return path


def test_clean_report_exits_zero(tmp_path: Path, caption_dot_rule) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\begin{figure}\n  \\caption{Схема установки}\n\\end{figure}\n", "utf-8")

    result = runner.invoke(app, ["check", str(path)])

    assert result.exit_code == EXIT_OK


def test_error_finding_exits_one(report: Path, caption_dot_rule) -> None:
    result = runner.invoke(app, ["check", str(report), "--format", "agent"])

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert "G732-6.5.7-caption-dot" in result.stdout
    assert "Убрать точку в конце подписи." in result.stdout


def test_quiet_prints_nothing(report: Path, caption_dot_rule) -> None:
    result = runner.invoke(app, ["check", str(report), "--quiet"])

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert result.stdout == ""


def test_ignore_switches_off_the_rule(report: Path, caption_dot_rule) -> None:
    result = runner.invoke(app, ["check", str(report), "--ignore", "G732-6.5.7-caption-dot"])

    assert result.exit_code == EXIT_OK


def test_missing_path_exits_two() -> None:
    result = runner.invoke(app, ["check", "нет-такого-файла.tex"])

    assert result.exit_code == EXIT_INTERNAL_ERROR


def test_unknown_rule_in_select_exits_two(report: Path, caption_dot_rule) -> None:
    result = runner.invoke(app, ["check", str(report), "--select", "G732-нет"])

    assert result.exit_code == EXIT_INTERNAL_ERROR
    assert "неизвестное правило 'G732-нет'" in result.output


def test_unknown_profile_exits_two(report: Path, caption_dot_rule) -> None:
    result = runner.invoke(app, ["check", str(report), "--profile", "нет-профиля"])

    assert result.exit_code == EXIT_INTERNAL_ERROR


def test_profile_disables_the_rule(tmp_path: Path, report: Path, caption_dot_rule) -> None:
    profile = tmp_path / "кафедра.toml"
    profile.write_text(
        'name = "Кафедра N"\nextends = "base"\ndisable = ["G732-6.5.7-caption-dot"]\n', "utf-8"
    )

    result = runner.invoke(app, ["check", str(report), "--profile", str(profile)])

    assert result.exit_code == EXIT_OK


def test_profile_lowers_severity(tmp_path: Path, report: Path, caption_dot_rule) -> None:
    profile = tmp_path / "кафедра.toml"
    profile.write_text(
        '[rules."G732-6.5.7-caption-dot"]\nseverity = "warning"\n',
        "utf-8",
    )

    result = runner.invoke(app, ["check", str(report), "--profile", str(profile), "-f", "agent"])

    assert result.exit_code == EXIT_OK
    assert "  warning  G732-6.5.7-caption-dot" in result.stdout


def test_json_output_is_parseable(report: Path, caption_dot_rule) -> None:
    import json

    result = runner.invoke(app, ["check", str(report), "--format", "json"])

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0"
    assert payload["summary"]["error"] == 1
    assert payload["findings"][0]["rule_id"] == "G732-6.5.7-caption-dot"


def test_rules_list_shows_the_registered_rule(caption_dot_rule) -> None:
    result = runner.invoke(app, ["rules", "list"])

    assert result.exit_code == EXIT_OK
    assert "G732-6.5.7-caption-dot" in result.stdout


def test_profile_show_reports_the_active_set(caption_dot_rule) -> None:
    result = runner.invoke(app, ["profile", "show"])

    assert result.exit_code == EXIT_OK
    assert "Правил включено: 1 из 1" in result.stdout
