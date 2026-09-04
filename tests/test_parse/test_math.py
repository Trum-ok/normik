from pathlib import Path

from nk.core.math import Math
from nk.parse.tex import parse


def math_of(tmp_path: Path, text: str) -> tuple[Math, Path]:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document.math, path


def masked(tmp_path: Path, text: str) -> list[str]:
    """Строки исходника, из которых убрана математика."""
    math, path = math_of(tmp_path, text)
    return [math.mask(path, lineno, line) for lineno, line in enumerate(text.splitlines(), start=1)]


def test_inline_math_is_masked(tmp_path: Path) -> None:
    assert masked(tmp_path, "текст $a - b$ дальше\n") == ["текст         дальше"]


def test_display_environment_is_masked_whole(tmp_path: Path) -> None:
    lines = masked(
        tmp_path,
        "\\begin{equation}\n\tx_p - x_q\n\t\\label{intra}\n\\end{equation}\nтекст\n",
    )

    assert [line.strip() for line in lines] == ["", "", "", "", "текст"]


def test_brackets_span_several_lines(tmp_path: Path) -> None:
    lines = masked(tmp_path, "до \\[\n\ty - z = 0\n\\] после\n")

    assert lines == ["до   ", "          ", "   после"]


def test_double_dollars_are_masked(tmp_path: Path) -> None:
    assert masked(tmp_path, "цена $$p - q$$ тут\n") == ["цена           тут"]


def test_parenthesis_form_is_masked(tmp_path: Path) -> None:
    assert masked(tmp_path, "форма \\( m - n \\) тут\n") == ["форма             тут"]


def test_escaped_dollar_does_not_open_a_formula(tmp_path: Path) -> None:
    assert masked(tmp_path, "цена 50\\$ - и дальше\n") == ["цена 50\\$ - и дальше"]


def test_line_break_with_an_option_is_not_a_formula(tmp_path: Path) -> None:
    """``\\\\[3pt]`` — перевод строки с отступом, а не начало выключной формулы."""
    assert masked(tmp_path, "строка \\\\[3pt] и - дефис\n") == ["строка \\\\[3pt] и - дефис"]


def test_dollar_inside_a_listing_does_not_open_a_formula(tmp_path: Path) -> None:
    text = "\\begin{lstlisting}\necho $PATH\n\\end{lstlisting}\nтекст - дальше\n"

    assert masked(tmp_path, text)[3] == "текст - дальше"


def test_unclosed_formula_ends_with_the_file(tmp_path: Path) -> None:
    math, path = math_of(tmp_path, "текст $a - b\nвторая строка\n")

    assert math.covers(path, 1, 8)
    assert math.covers(path, 2, 1)
