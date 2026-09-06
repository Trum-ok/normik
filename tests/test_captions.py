"""Подпись с меткой внутри: текст берётся без метки, правка её сохраняет."""

from pathlib import Path

from nk.core.fixer import plan
from nk.core.registry import load_rules
from nk.parse.tex import parse

DOT = "figure-caption-dot"


def fixed(tmp_path: Path, rule_id: str, text: str) -> str:
    path = tmp_path / "report.tex"
    path.write_text(text, encoding="utf-8")
    document = parse([path]).document
    findings = list(load_rules().get(rule_id)(document))
    assert len(findings) == 1
    (edit,) = plan(findings).edits
    return edit.text


def test_label_inside_the_caption_survives_the_fix(tmp_path: Path) -> None:
    text = fixed(
        tmp_path, DOT, "\\begin{figure}\n\\caption{Схема установки.\\label{fig:a}}\n\\end{figure}\n"
    )
    assert "\\caption{Схема установки\\label{fig:a}}" in text


def test_short_form_and_captionof_type_survive_the_fix(tmp_path: Path) -> None:
    text = fixed(
        tmp_path,
        DOT,
        "\\begin{figure}\n\\captionof{figure}[Схема]{Схема установки.}\n\\end{figure}\n",
    )
    assert "\\captionof{figure}[Схема]{Схема установки}" in text
