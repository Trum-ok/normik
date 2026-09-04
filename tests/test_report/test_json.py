import json as stdlib_json

from nk.core.runner import RunResult
from nk.report import json as json_report

EXPECTED = {
    "schema_version": "1.2",
    "tool": {"name": "nk", "version": "0.1.0"},
    "profile": "base",
    "summary": {"error": 1, "warning": 1, "info": 1, "files_checked": 12, "fixable": 0},
    "suppressed": {"inline": 0, "baseline": 0},
    "findings": [
        {
            "rule_id": "G732-6.2.4-heading-hyphenation",
            "clause": "6.2.4",
            "severity": "info",
            "message": "Подпись рисунка заканчивается точкой и использует дефис вместо тире",
            "requirement": "Форма «Рисунок N — Название», тире с пробелами, без точки в конце",
            "path": "chapters/01-intro.tex",
            "lineno": 12,
            "col": 3,
            "excerpt": "  \\caption{Схема экспериментальной установки.}",
            "context": [
                "\\begin{figure}[h]",
                "  \\includegraphics{img/setup.png}",
                "  \\caption{Схема экспериментальной установки.}",
                "\\end{figure}",
                "",
            ],
            "suggestion": "\\caption{Схема экспериментальной установки}",
            "fixable": False,
        },
        {
            "rule_id": "G732-6.5.7-caption-dot",
            "clause": "6.5.7",
            "severity": "error",
            "message": "Подпись рисунка заканчивается точкой и использует дефис вместо тире",
            "requirement": "Форма «Рисунок N — Название», тире с пробелами, без точки в конце",
            "path": "chapters/02-method.tex",
            "lineno": 145,
            "col": 3,
            "excerpt": "  \\caption{Схема экспериментальной установки.}",
            "context": [
                "\\begin{figure}[h]",
                "  \\includegraphics{img/setup.png}",
                "  \\caption{Схема экспериментальной установки.}",
                "\\end{figure}",
                "",
            ],
            "suggestion": "\\caption{Схема экспериментальной установки}",
            "fixable": False,
        },
        {
            "rule_id": "G732-6.6.2-table-no-reference",
            "clause": "6.6.2",
            "severity": "warning",
            "message": "Подпись рисунка заканчивается точкой и использует дефис вместо тире",
            "requirement": "Форма «Рисунок N — Название», тире с пробелами, без точки в конце",
            "path": "chapters/02-method.tex",
            "lineno": 160,
            "col": None,
            "excerpt": "  \\caption{Схема экспериментальной установки.}",
            "context": [
                "\\begin{figure}[h]",
                "  \\includegraphics{img/setup.png}",
                "  \\caption{Схема экспериментальной установки.}",
                "\\end{figure}",
                "",
            ],
            "suggestion": "\\caption{Схема экспериментальной установки}",
            "fixable": False,
        },
    ],
    "failed_rules": [{"rule_id": "G732-плохое", "error": "ValueError: сломалось"}],
}


def test_json_snapshot(result: RunResult) -> None:
    assert stdlib_json.loads(json_report.render(result)) == EXPECTED


def test_output_is_utf8_not_escaped(result: RunResult) -> None:
    text = json_report.render(result)
    assert "Подпись рисунка" in text
    assert "\\u04" not in text


def test_output_ends_with_a_newline(result: RunResult) -> None:
    assert json_report.render(result).endswith("}\n")
