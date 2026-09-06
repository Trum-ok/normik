import json
from collections.abc import Iterable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nk.cli import EXIT_FOUND_ERRORS, EXIT_INTERNAL_ERROR, EXIT_OK, app
from nk.core.document import Document
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.rule import RuleRegistry, rule
from nk.core.standards import G732

RULE_ID = "figure-caption-dot"

runner = CliRunner()


FIGURE = """\
Схема установки приведена на рисунке~\\ref{fig:setup}.

\\begin{figure}
  \\includegraphics{img/setup.png}
  \\caption{Схема установки%s}
  \\label{fig:setup}
\\end{figure}
"""


@pytest.fixture
def report(tmp_path: Path) -> Path:
    """Отчёт ровно с одним нарушением — точкой в конце наименования рисунка."""
    path = tmp_path / "report.tex"
    path.write_text(FIGURE % ".", encoding="utf-8")
    return path


@pytest.fixture
def clean_report(tmp_path: Path) -> Path:
    path = tmp_path / "clean.tex"
    path.write_text(FIGURE % "", encoding="utf-8")
    return path


@pytest.fixture
def failing_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """Реестр из одного правила, которое падает с исключением."""
    registry = RuleRegistry()

    @rule(
        id="G732-6.5.7-падает",
        standards={G732: "6.5.7"},
        severity=Severity.ERROR,
        title="падает",
        registry=registry,
    )
    def explode(doc: Document) -> Iterable[Finding]:
        raise ValueError("сломалось")

    monkeypatch.setattr("nk.cli.load_rules", lambda: registry)


@pytest.mark.usefixtures("failing_rule")
def test_failed_rule_exits_two(clean_report: Path) -> None:
    result = runner.invoke(app, ["check", str(clean_report)])

    assert result.exit_code == EXIT_INTERNAL_ERROR
    assert "G732-6.5.7-падает упало и пропущено" in result.stdout


@pytest.mark.usefixtures("failing_rule")
def test_failed_rule_blocks_baseline(clean_report: Path, tmp_path: Path) -> None:
    snapshot = tmp_path / "baseline.json"

    result = runner.invoke(app, ["check", str(clean_report), "--write-baseline", str(snapshot)])

    assert result.exit_code == EXIT_INTERNAL_ERROR
    assert not snapshot.exists()
    assert "G732-6.5.7-падает упало и пропущено" in result.output


@pytest.mark.usefixtures("failing_rule")
def test_failed_rule_exits_two_with_diff(clean_report: Path) -> None:
    result = runner.invoke(app, ["check", str(clean_report), "--diff"])

    assert result.exit_code == EXIT_INTERNAL_ERROR
    assert "G732-6.5.7-падает упало и пропущено" in result.output


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


def test_pyproject_section_is_found_automatically(tmp_path: Path, report: Path) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text(
        f'[project]\nname = "diploma"\n\n[tool.nk]\ndisable = ["{RULE_ID}"]\n', "utf-8"
    )

    assert runner.invoke(app, ["check", str(report)]).exit_code == EXIT_OK


def test_explicit_profile_wins_over_the_found_config(tmp_path: Path, report: Path) -> None:
    config = tmp_path / "nk.toml"
    config.write_text(f'disable = ["{RULE_ID}"]\n', "utf-8")

    result = runner.invoke(app, ["check", str(report), "--profile", "base"])
    assert result.exit_code == EXIT_FOUND_ERRORS


def test_json_output_is_parseable(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--format", "json"])

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.3"
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
    assert "nk.rules.figures.figure_caption_dot" in result.stdout


def test_profile_show_lists_the_active_set() -> None:
    result = runner.invoke(app, ["profile", "show"])

    assert result.exit_code == EXIT_OK
    assert "Профиль: base" in result.stdout
    assert "Файл: встроенный" in result.stdout
    assert "Стандарт: ГОСТ 7.32-2017" in result.stdout
    assert RULE_ID in result.stdout


def test_inline_suppression_lowers_exit_code(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text(FIGURE % "." + "% nk: ignore-file " + RULE_ID + "\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--format", "agent"])

    assert result.exit_code == EXIT_OK
    assert "Скрыто подавлениями в исходниках: 1." in result.stdout


def test_unused_suppression_is_warned_about(clean_report: Path, tmp_path: Path) -> None:
    path = tmp_path / "unused.tex"
    path.write_text(clean_report.read_text(encoding="utf-8") + f"% nk: ignore {RULE_ID}\n", "utf-8")

    result = runner.invoke(app, ["check", str(path), "--format", "agent"])

    assert result.exit_code == EXIT_OK
    assert "NK-IGNORE-001" in result.stdout


def test_internal_code_can_be_ignored(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\input{нет-такого}\n", encoding="utf-8")

    with_code = runner.invoke(app, ["check", str(path), "--format", "agent"])
    without_code = runner.invoke(
        app, ["check", str(path), "--format", "agent", "--ignore", "NK-PARSE-001"]
    )

    assert "NK-PARSE-001" in with_code.stdout
    assert "NK-PARSE-001" not in without_code.stdout


def test_profile_can_disable_an_internal_code(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\input{нет-такого}\n", encoding="utf-8")
    profile = tmp_path / "кафедра.toml"
    profile.write_text('disable = ["NK-PARSE-001"]\n', encoding="utf-8")

    result = runner.invoke(
        app, ["check", str(path), "--profile", str(profile), "--format", "agent"]
    )

    assert result.exit_code == EXIT_OK
    assert "NK-PARSE-001" not in result.stdout


def test_baseline_round_trip(report: Path, tmp_path: Path) -> None:
    snapshot = tmp_path / ".nk-baseline.json"

    written = runner.invoke(app, ["check", str(report), "--write-baseline", str(snapshot)])
    assert written.exit_code == EXIT_OK
    assert snapshot.is_file()

    filtered = runner.invoke(
        app, ["check", str(report), "--baseline", str(snapshot), "--format", "agent"]
    )
    assert filtered.exit_code == EXIT_OK
    assert "Скрыто" in filtered.stdout
    assert RULE_ID not in filtered.stdout


def test_baseline_survives_a_line_shift(report: Path, tmp_path: Path) -> None:
    snapshot = tmp_path / ".nk-baseline.json"
    runner.invoke(app, ["check", str(report), "--write-baseline", str(snapshot)])
    report.write_text("Вводный абзац.\n\n" + report.read_text(encoding="utf-8"), encoding="utf-8")

    result = runner.invoke(app, ["check", str(report), "--baseline", str(snapshot)])

    assert result.exit_code == EXIT_OK


def test_baseline_reports_a_new_violation(report: Path, tmp_path: Path) -> None:
    snapshot = tmp_path / ".nk-baseline.json"
    runner.invoke(app, ["check", str(report), "--write-baseline", str(snapshot)])
    report.write_text(
        report.read_text(encoding="utf-8")
        + "\n\\begin{figure}\n  \\includegraphics{img/p.png}\n  \\caption{Новая подпись.}\n\\end{figure}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["check", str(report), "--baseline", str(snapshot), "--format", "agent"]
    )

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert "Новая подпись" in result.stdout


def test_broken_baseline_exits_two(report: Path, tmp_path: Path) -> None:
    snapshot = tmp_path / "битый.json"
    snapshot.write_text("{не json", encoding="utf-8")

    result = runner.invoke(app, ["check", str(report), "--baseline", str(snapshot)])

    assert result.exit_code == EXIT_INTERNAL_ERROR


def test_fix_rewrites_the_source(report: Path) -> None:
    result = runner.invoke(app, ["check", str(report), "--fix"])

    assert result.exit_code == EXIT_OK
    assert "Исправлено находок: 1." in result.stdout
    assert "\\caption{Схема установки}" in report.read_text(encoding="utf-8")


def test_fix_converges_over_several_passes(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text(
        "Схема приведена на рисунке~\\ref{fig:a}.\n\n"
        "\\begin{figure}\n"
        "  \\includegraphics{img/a.png}\n"
        "  \\caption{Рисунок 1 — схема экспе\\-риментальной установки.}\n"
        "  \\label{fig:a}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(path), "--fix"])

    assert result.exit_code == EXIT_OK
    assert "\\caption{Схема экспериментальной установки}" in path.read_text(encoding="utf-8")


def test_write_protected_source_is_reported_not_changed(report: Path) -> None:
    before = report.read_text(encoding="utf-8")
    report.chmod(0o444)

    result = runner.invoke(app, ["check", str(report), "--fix"])

    assert "Не удалось записать" in result.output
    assert "Правки применены не полностью" in result.output
    assert report.read_text(encoding="utf-8") == before


def test_fix_reports_a_rule_opened_by_a_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Правка, открывающая нарушение другого правила, не проходит молча."""
    registry = RuleRegistry()

    @rule(
        id="G732-6.5.7-точка-тест",
        standards={G732: "6.5.7"},
        severity=Severity.ERROR,
        title="Точка в наименовании",
        fixable=True,
        registry=registry,
    )
    def caption_dot(doc: Document) -> Iterable[Finding]:
        for line in doc.iter_lines():
            if line.stripped.endswith("."):
                yield caption_dot.finding(
                    doc,
                    line,
                    message="Наименование заканчивается точкой.",
                    requirement="Наименование приводят без точки в конце.",
                    suggestion="Убрать точку.",
                    fix=Fix(
                        Region.in_line(
                            line.path, line.lineno, len(line.stripped), len(line.stripped) + 1
                        ),
                        "!",
                    ),
                )

    @rule(
        id="G732-6.5.8-восклицание-тест",
        standards={G732: "6.5.8"},
        severity=Severity.ERROR,
        title="Восклицание в наименовании",
        registry=registry,
    )
    def caption_capital(doc: Document) -> Iterable[Finding]:
        for line in doc.iter_lines():
            if line.stripped.endswith("!"):
                yield caption_capital.finding(
                    doc,
                    line,
                    message="Наименование заканчивается восклицательным знаком.",
                    requirement="Наименование приводят без восклицательного знака.",
                    suggestion="Убрать восклицательный знак.",
                )

    monkeypatch.setattr("nk.cli.load_rules", lambda: registry)
    path = tmp_path / "report.tex"
    path.write_text("Наименование рисунка.\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--fix"])

    assert "Правки открыли нарушения, которых не было" in result.output
    assert "G732-6.5.8-восклицание-тест" in result.output


def test_diff_leaves_the_source_alone(report: Path) -> None:
    before = report.read_text(encoding="utf-8")

    result = runner.invoke(app, ["check", str(report), "--diff"])

    assert result.exit_code == EXIT_OK
    assert "-  \\caption{Схема установки.}" in result.stdout
    assert "+  \\caption{Схема установки}" in result.stdout
    assert report.read_text(encoding="utf-8") == before


def test_diff_shows_every_pass(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text("\\section{1. Методика проведения работы.}\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--diff"])

    assert "+\\section{Методика проведения работы}" in result.stdout


def test_fix_leaves_unfixable_findings(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_text(
        "\\begin{figure}\n  \\includegraphics{img/a.png}\n"
        "  \\caption{Схема установки.}\n\\end{figure}\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(path), "--fix", "--format", "agent"])

    assert result.exit_code == EXIT_FOUND_ERRORS
    assert "figure-no-reference" in result.stdout
    assert "\\caption{Схема установки}" in path.read_text(encoding="utf-8")


def test_fix_respects_suppressions(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    original = (
        "Схема приведена на рисунке~\\ref{fig:a}.\n\n"
        "\\begin{figure}\n"
        "  \\includegraphics{img/a.png}\n"
        "  \\caption{Схема установки.} % nk: ignore figure-caption-dot\n"
        "  \\label{fig:a}\n"
        "\\end{figure}\n"
    )
    path.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["check", str(path), "--fix"])

    assert result.exit_code == EXIT_OK
    assert path.read_text(encoding="utf-8") == original
