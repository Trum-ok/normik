from pathlib import Path

from nk.core.finding import Finding, Severity


def make_finding(
    rule_id: str = "figure-caption-dot",
    *,
    clause: str = "6.5.7",
    source: str = "ГОСТ 7.32-2017",
    severity: Severity = Severity.ERROR,
    path: str = "chapters/02-method.tex",
    lineno: int = 145,
    col: int | None = 3,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        clause=clause,
        source=source,
        severity=severity,
        message="Подпись рисунка заканчивается точкой и использует дефис вместо тире",
        requirement="Форма «Рисунок N — Название», тире с пробелами, без точки в конце",
        path=Path(path),
        lineno=lineno,
        col=col,
        excerpt="  \\caption{Схема экспериментальной установки.}",
        context=(
            "\\begin{figure}[h]",
            "  \\includegraphics{img/setup.png}",
            "  \\caption{Схема экспериментальной установки.}",
            "\\end{figure}",
            "",
        ),
        suggestion="\\caption{Схема экспериментальной установки}",
    )
