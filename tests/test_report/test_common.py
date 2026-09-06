from dataclasses import replace
from pathlib import Path

from helpers import make_finding

from nk.core.finding import Fix
from nk.core.position import Region
from nk.core.runner import RunResult
from nk.report.common import caret_line, context_lines, fixable_line

FIX = Fix(region=Region.in_line(Path("report.tex"), 145, 3, 4), replacement="—")


def test_caret_stands_under_the_column() -> None:
    finding = make_finding(col=5)

    assert caret_line(finding, "abcdefg") == "    ^"


def test_finding_without_a_column_gets_no_caret() -> None:
    assert caret_line(make_finding(col=None), "abcdefg") is None


def test_column_beyond_the_shown_text_gets_no_caret() -> None:
    """Фрагмент строки в выводе урезан: указывать в пустоту хуже, чем не указывать."""
    assert caret_line(make_finding(col=200), "короткая строка") is None


def test_caret_may_stand_right_after_the_last_character() -> None:
    assert caret_line(make_finding(col=8), "abcdefg") == "       ^"


def test_no_caret_under_the_start_of_a_command() -> None:
    """Нарушение всей записи, а не знака: стрелка слева уже показала строку."""
    assert caret_line(make_finding(col=2), "\t\\bibitem{bs} BeautifulSoup") is None


def test_tabs_are_kept_in_the_indent() -> None:
    """Табуляция занимает не один знак, иначе указатель уезжает."""
    assert caret_line(make_finding(col=3), "\t\tтекст") == "\t\t^"


def test_caret_stays_one_character_even_when_the_fix_is_wider() -> None:
    """Правило знает точку нарушения, а не его границы: область правки шире."""
    finding = make_finding(lineno=1, col=3)
    finding = replace(
        finding,
        fix=Fix(region=Region.in_line(Path("report.tex"), 1, 3, 8), replacement="рисунок"),
    )

    assert caret_line(finding, "на рис. 1") == "  ^"


def test_fixable_line_counts_and_offers_the_command() -> None:
    result = RunResult(
        profile="base",
        findings=(replace(make_finding(), fix=FIX), make_finding(rule_id="G732-другое")),
    )

    assert fixable_line(result, "nk check report.tex") == (
        "Исправимо машинно: 1 из 2. Применить: nk check report.tex --fix, "
        "посмотреть правки: --diff."
    )


def test_no_fixable_line_when_nothing_is_fixable() -> None:
    result = RunResult(profile="base", findings=(make_finding(),))

    assert fixable_line(result, "nk check report.tex") is None


def test_fix_is_not_offered_twice() -> None:
    """Ключ уже отдан: оставшееся им не берётся, советовать его снова незачем."""
    result = RunResult(profile="base", findings=(replace(make_finding(), fix=FIX),))

    assert fixable_line(result, "nk check report.tex --fix") == "Исправимо машинно: 1 из 1."


def test_caret_follows_the_window_of_a_long_line() -> None:
    """Строку сокращают окном вокруг нарушения, и указатель обязан ехать вместе с ним."""
    line = "a" * 200 + "цель" + "b" * 200
    finding = replace(
        make_finding(col=201),
        lineno=1,
        excerpt=line,
        context=(line,),
    )

    shown = list(context_lines(finding, limit=60))

    source, caret = shown[0].text, shown[1].text
    assert "цель" in source
    assert source[caret.index("^")] == "ц"


def test_neighbours_are_cut_from_the_start() -> None:
    """Соседней строке окно не нужно: нарушения в ней нет."""
    finding = replace(
        make_finding(col=1),
        lineno=2,
        context=("n" * 200, "hit", "n" * 200),
    )

    shown = [item.text for item in context_lines(finding, limit=40)]

    assert shown[0].startswith("n") and shown[0].endswith("…")
