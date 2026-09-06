"""Изложение от первого лица: местоимения и глаголы."""

from support import make_document

from nk.core.profile import Profile
from nk.core.registry import load_rules

PRONOUN = "first-person-pronoun"
VERB = "first-person-verb"


def findings(text: str, rule_id: str, plural: bool = False) -> list:
    profile = Profile(params={rule_id: {"plural": plural}})
    document = make_document(text, profile=profile)
    return list(load_rules().get(rule_id)(document))


def test_authorial_we_is_ignored_by_default() -> None:
    """Авторское «мы» одни руководители запрещают, другие требуют."""
    assert findings("Мы рассмотрели устойчивость системы.\n", PRONOUN) == []
    assert findings("Рассмотрим устойчивость системы.\n", VERB) == []


def test_parameter_turns_the_authorial_we_on() -> None:
    assert [f.lineno for f in findings("Мы рассмотрели систему.\n", PRONOUN, plural=True)] == [1]
    assert [f.lineno for f in findings("Рассмотрим систему.\n", VERB, plural=True)] == [1]


def test_enumeration_label_is_not_a_pronoun() -> None:
    assert findings("\\item[я)] последний элемент перечисления.\n", PRONOUN) == []


def test_appendix_letter_is_not_a_pronoun() -> None:
    assert findings("Протокол измерений вынесен в ПРИЛОЖЕНИЕ Я.\n", PRONOUN) == []


def test_pronoun_at_the_start_of_a_sentence_is_found() -> None:
    assert [f.col for f in findings("Стенд собран. Я снял показания.\n", PRONOUN)] == [15]


def test_command_opens_a_sentence() -> None:
    """После `\\item` подлежащего нет: глагол читается как «я изучил»."""
    assert [f.lineno for f in findings("\\item Изучил документооборот.\n", VERB)] == [1]


def test_verb_with_a_subject_is_not_first_person() -> None:
    assert findings("Руководитель практики провёл инструктаж.\n", VERB) == []
