from dataclasses import replace
from pathlib import Path

from helpers import make_finding

from nk.core.finding import Fix
from nk.core.position import Region
from nk.report.common import caret_line


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
