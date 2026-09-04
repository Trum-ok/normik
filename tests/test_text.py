"""Текст строки, из которого правила типографики видят только прозу."""

from support import make_document

from nk.rules._text import prose


def masked(text: str) -> str:
    document = make_document(text)
    return prose(document, document.lines[0])


def test_literal_argument_is_masked_but_keeps_the_line_length() -> None:
    line = "текст \\verb|И. И. Иванов| хвост"

    assert masked(line) == "текст \\verb" + " " * 15 + "хвост"
    assert len(masked(line)) == len(line)


def test_unclosed_literal_runs_to_the_end_of_the_line() -> None:
    assert masked("\\verb|И. И. Иванов") == "\\verb" + " " * 13


def test_command_that_only_starts_like_verb_is_left_alone() -> None:
    assert masked("\\verbatim И. И. Иванов") == "\\verbatim И. И. Иванов"


def test_typewriter_argument_is_masked_and_the_rest_of_the_line_is_not() -> None:
    assert masked("Файл \\texttt{a - b} и c - d") == "Файл \\texttt" + " " * 8 + "и c - d"
