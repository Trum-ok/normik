import pytest
from rich.console import Console

from nk.core.runner import RunResult
from nk.report import human


@pytest.fixture
def plain() -> Console:
    return Console(width=120, no_color=True, force_terminal=False, legacy_windows=False)


def capture(console: Console, result: RunResult) -> str:
    with console.capture() as captured:
        human.render(result, console)
    return captured.get()


def test_findings_are_grouped_by_file(plain: Console, result: RunResult) -> None:
    text = capture(plain, result)
    assert text.index("chapters/01-intro.tex") < text.index("chapters/02-method.tex")


def test_violating_line_is_marked_without_colour(plain: Console, result: RunResult) -> None:
    text = capture(plain, result)
    assert "> 145 |   \\caption{Схема экспериментальной установки.}" in text
    assert "  144 |   \\includegraphics{img/setup.png}" in text


def test_every_finding_answers_the_three_questions(plain: Console, result: RunResult) -> None:
    text = capture(plain, result)
    assert text.count("Нарушение:") == 3
    assert text.count("Требуется:") == 3
    assert text.count("Исправить:") == 3


def test_summary_and_failed_rules(plain: Console, result: RunResult) -> None:
    text = capture(plain, result)
    assert "Итого: 1 error, 1 warning, 1 info." in text
    assert "Правило G732-плохое упало и пропущено: ValueError: сломалось" in text


def test_hint_about_machine_output(plain: Console, result: RunResult) -> None:
    assert "--format json" in capture(plain, result)


def test_empty_result_prints_only_the_summary(plain: Console) -> None:
    text = capture(plain, RunResult(profile="base", findings=(), files_checked=3))
    assert "Итого: 0 error, 0 warning, 0 info." in text
    assert "--format json" not in text


def test_caret_points_at_the_place_without_colour(plain: Console, result: RunResult) -> None:
    text = capture(plain, result)
    assert "> 145 |   \\caption{Схема экспериментальной установки.}" in text
    assert "      |   ^" in text
