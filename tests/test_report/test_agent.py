from dataclasses import replace

from helpers import make_finding

from nk.core.finding import Severity
from nk.core.runner import RunResult
from nk.report import agent

EXPECTED = """\
Команда: nk check chapters --format agent
Профиль: base, файлов проверено: 12

chapters/01-intro.tex:12:3  info  heading-hyphenation  (ГОСТ 7.32-2017 п. 6.2.4)
  Нарушение: Подпись рисунка заканчивается точкой и использует дефис вместо тире
  Требуется: Форма «Рисунок N — Название», тире с пробелами, без точки в конце
  Исправить: \\caption{Схема экспериментальной установки}
  Контекст:
    10 | \\begin{figure}[h]
    11 |   \\includegraphics{img/setup.png}
    12 |   \\caption{Схема экспериментальной установки.}
    13 | \\end{figure}
    14 |

chapters/02-method.tex:145:3  error  figure-caption-dot  (ГОСТ 7.32-2017 п. 6.5.7)
  Нарушение: Подпись рисунка заканчивается точкой и использует дефис вместо тире
  Требуется: Форма «Рисунок N — Название», тире с пробелами, без точки в конце
  Исправить: \\caption{Схема экспериментальной установки}
  Контекст:
    143 | \\begin{figure}[h]
    144 |   \\includegraphics{img/setup.png}
    145 |   \\caption{Схема экспериментальной установки.}
    146 | \\end{figure}
    147 |

chapters/02-method.tex:160  warning  table-no-reference  (ГОСТ 7.32-2017 п. 6.6.2)
  Нарушение: Подпись рисунка заканчивается точкой и использует дефис вместо тире
  Требуется: Форма «Рисунок N — Название», тире с пробелами, без точки в конце
  Исправить: \\caption{Схема экспериментальной установки}
  Контекст:
    158 | \\begin{figure}[h]
    159 |   \\includegraphics{img/setup.png}
    160 |   \\caption{Схема экспериментальной установки.}
    161 | \\end{figure}
    162 |

Итого: 1 error, 1 warning, 1 info.
Правило G732-плохое упало и пропущено: ValueError: сломалось
"""


def test_agent_snapshot(result: RunResult) -> None:
    assert agent.render(result, command="nk check chapters --format agent") == EXPECTED


def test_output_has_no_ansi_or_pseudographics(result: RunResult) -> None:
    text = agent.render(result, command="nk check .")
    assert "\x1b" not in text
    assert not set(text) & set("─│┌┐└┘━┃╭╮╰╯")


def test_limit_keeps_every_error(result: RunResult) -> None:
    many = RunResult(
        profile="base",
        findings=tuple(
            make_finding(f"G732-{i}", severity=Severity.ERROR if i % 2 else Severity.INFO, lineno=i)
            for i in range(1, 21)
        ),
        files_checked=1,
    )

    text = agent.render(many, command="nk check .", limit=12)

    assert text.count("  error  ") == 10
    assert "Скрыто находок: 8. Показать все: --limit 0." in text


def test_zero_limit_shows_everything(result: RunResult) -> None:
    text = agent.render(result, command="nk check .", limit=0)
    assert "Скрыто" not in text


def test_multiline_suggestion_stays_a_block() -> None:
    finding = replace(make_finding(), suggestion="\\begin{figure}\n\\end{figure}")
    text = agent.render(RunResult(profile="base", findings=(finding,)), command="nk check .")

    assert "  Исправить:\n    \\begin{figure}\n    \\end{figure}\n" in text
