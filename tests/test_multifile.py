"""Правила о структуре на отчёте, разложенном по файлам.

Фикстуры правил однофайловые, а именно многофайловый отчёт с макросами шаблона —
обычная форма реальной работы, поэтому такие случаи проверяются отдельно.
"""

from pathlib import Path

from nk.core.registry import load_rules
from nk.parse.tex import parse

TEMPLATE = {
    "преамбула.tex": (
        "\\documentclass{extreport}\n"
        "\\newcommand{\\ssr}[1]{\\begin{center}\n"
        "\\LARGE\\bfseries{#1}\n"
        "\\end{center} \\addcontentsline{toc}{chapter}{#1}}\n"
    ),
    "титул.tex": "Титульный лист.\n",
    "реферат.tex": "\\ssr{РЕФЕРАТ}\nОтчёт 45 с., 3 рис., 5 табл., 7 источников, 1 прил.\n",
    "введение.tex": "\\ssr{ВВЕДЕНИЕ}\nАктуальность темы.\n",
    "основная.tex": "\\chapter{Выбор направления исследований}\nОсновная часть.\n",
    "заключение.tex": "\\ssr{ЗАКЛЮЧЕНИЕ}\nКраткие выводы.\n",
    "источники.tex": (
        "\\addcontentsline{toc}{chapter}{СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ}\n"
        "\\begin{thebibliography}{}\n\\bibitem{lit1} Источник.\n\\end{thebibliography}\n"
    ),
    "отчёт.tex": (
        "\\input{преамбула}\n"
        "\\begin{document}\n"
        "\\include{титул}\n"
        "\\include{реферат}\n"
        "\\tableofcontents\n"
        "\\include{введение}\n"
        "\\include{основная}\n"
        "\\include{заключение}\n"
        "\\include{источники}\n"
        "\\end{document}\n"
    ),
}


def build(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path


def findings(tmp_path: Path, rule_id: str, files: dict[str, str] | None = None) -> list:
    document = parse([build(tmp_path, files or TEMPLATE)]).document
    return list(load_rules().get(rule_id)(document))


def test_structural_elements_set_by_a_template_macro_are_found(tmp_path: Path) -> None:
    assert findings(tmp_path, "required-element-missing") == []


def test_element_order_follows_the_includes_not_the_file_names(tmp_path: Path) -> None:
    assert findings(tmp_path, "elements-order") == []


def test_missing_element_is_still_reported(tmp_path: Path) -> None:
    files = dict(TEMPLATE)
    del files["введение.tex"]
    files["отчёт.tex"] = files["отчёт.tex"].replace("\\include{введение}\n", "")

    found = findings(tmp_path, "required-element-missing", files)

    assert [finding.message for finding in found] == [
        "В отчёте нет структурного элемента «ВВЕДЕНИЕ»."
    ]


def test_order_violation_between_files_is_reported(tmp_path: Path) -> None:
    files = dict(TEMPLATE)
    files["отчёт.tex"] = files["отчёт.tex"].replace(
        "\\include{введение}\n\\include{основная}\n\\include{заключение}\n",
        "\\include{заключение}\n\\include{основная}\n\\include{введение}\n",
    )

    found = findings(tmp_path, "elements-order", files)

    assert [finding.message for finding in found] == [
        "Элемент «ВВЕДЕНИЕ» стоит после «ЗАКЛЮЧЕНИЕ»."
    ]
    assert found[0].path.name == "введение.tex"
