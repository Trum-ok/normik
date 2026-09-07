"""Библиографическое описание, собранное из исходника."""

from pathlib import Path

from nk.core.document import Document
from nk.parse.tex import parse
from nk.rules._bibliography import entries
from nk.rules.bibliography.bibitem_area_separator import bibitem_area_separator
from nk.rules.bibliography.bibitem_final_dot import bibitem_final_dot
from nk.rules.bibliography.bibitem_prescribed_spacing import bibitem_prescribed_spacing


def read(tmp_path: Path, text: str) -> Document:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    return parse([path]).document


def listed(tmp_path: Path, *lines: str) -> Document:
    body = "".join(f"{line}\n" for line in lines)
    return read(tmp_path, f"\\begin{{thebibliography}}{{9}}\n{body}\\end{{thebibliography}}\n")


def texts(tmp_path: Path, *lines: str) -> list[str]:
    return [entry.text.strip() for entry in entries(listed(tmp_path, *lines))]


def test_description_of_several_lines_is_read_as_one(tmp_path: Path) -> None:
    """Перенос строки описание не рвёт: элемент не обязан умещаться в строку."""
    assert texts(
        tmp_path,
        "\\bibitem{ivanov} Иванов, И.~И. Методика измерений :",
        "пособие. – Москва : Наука, 2020.",
    ) == ["Иванов, И. И. Методика измерений : пособие. – Москва : Наука, 2020."]


def test_two_descriptions_in_one_line_do_not_mix(tmp_path: Path) -> None:
    assert texts(tmp_path, "\\bibitem{a} Первое. \\bibitem{b} Второе.") == ["Первое.", "Второе."]


def test_markup_is_dropped_and_the_address_is_kept(tmp_path: Path) -> None:
    """Имя команды и скобки не печатаются, а адрес внутри них — часть описания.

    Разметка именно выбрасывается: забей её пробелами — и закрывающая скобка
    ``\\url{…}`` дала бы пробел перед точкой, которого в наборе нет.
    """
    assert texts(tmp_path, "\\bibitem{site} \\emph{Сайт}. – URL: \\url{https://a.ru}.") == [
        "Сайт. – URL: https://a.ru."
    ]


def test_empty_description_gives_no_findings(tmp_path: Path) -> None:
    """У записи без описания закрывать точкой нечего."""
    assert list(bibitem_final_dot(listed(tmp_path, "\\bibitem{empty}"))) == []


def test_bibtex_list_is_out_of_reach(tmp_path: Path) -> None:
    """Описаний в исходнике нет: об этом сообщает bibtex-order-unverifiable."""
    assert list(entries(read(tmp_path, "\\bibliography{refs}\n"))) == []


def test_separator_broken_by_a_line_break_is_reported_without_a_fix(tmp_path: Path) -> None:
    """Правка склеила бы строки исходника, а нарушение остаётся нарушением."""
    doc = listed(
        tmp_path,
        "\\bibitem{ivanov} Иванов, И.~И. Методика измерений.",
        "--- Москва : Наука, 2020.",
    )

    findings = list(bibitem_area_separator(doc))

    assert [(finding.lineno, finding.fix) for finding in findings] == [(2, None)]


def test_escaped_sign_keeps_only_the_sign(tmp_path: Path) -> None:
    """Обратной косой в наборе не видно, а знак за ней — часть описания."""
    assert texts(tmp_path, "\\bibitem{a} Рост 30~\\% за год. – Москва, 2020.") == [
        "Рост 30 % за год. – Москва, 2020."
    ]


def test_separator_at_the_end_of_a_line_is_fixed_without_the_space(tmp_path: Path) -> None:
    """Пробел за тире даёт сам перенос: править его не нужно и нечем."""
    doc = listed(
        tmp_path,
        "\\bibitem{ivanov} Иванов, И.~И. Методика измерений. —",
        "Москва : Наука, 2020.",
    )

    findings = list(bibitem_area_separator(doc))
    fixes = [finding.fix for finding in findings]

    assert [finding.lineno for finding in findings] == [2]
    assert fixes[0] is not None
    assert fixes[0].replacement == ". –"


def test_closing_brace_is_not_a_space_before_the_dot(tmp_path: Path) -> None:
    """Скобка группы не печатается: пробела перед точкой в наборе нет."""
    doc = listed(tmp_path, "\\bibitem{site} Сайт. – URL: \\url{https://a.ru}.")

    assert list(bibitem_prescribed_spacing(doc)) == []


def test_final_dot_goes_after_the_markup(tmp_path: Path) -> None:
    """Внутри ``\\url{…}`` точка напечаталась бы частью адреса."""
    doc = listed(tmp_path, "\\bibitem{site} Сайт. – URL: \\url{https://a.ru}")

    fixes = [finding.fix for finding in bibitem_final_dot(doc)]

    assert len(fixes) == 1
    assert fixes[0] is not None
    assert fixes[0].region.start.col == len("\\bibitem{site} Сайт. – URL: \\url{https://a.ru}") + 1


def test_dot_before_another_sign_needs_no_space(tmp_path: Path) -> None:
    """Пробелом отделяют знак от текста, а не от другого знака (п. 4.6.11)."""
    doc = listed(
        tmp_path,
        "\\bibitem{a} Методика ... измерений / Иванов, И.~И. [и др.]. –",
        "Москва : Наука, 2020. – 120~с.",
    )

    assert list(bibitem_prescribed_spacing(doc)) == []


def test_dot_before_a_word_still_needs_one(tmp_path: Path) -> None:
    doc = listed(tmp_path, "\\bibitem{a} Иванов, И.И. Методика. – Москва, 2020.")

    messages = [finding.message for finding in bibitem_prescribed_spacing(doc)]

    assert messages == ["После знака «.» нет пробела."]
