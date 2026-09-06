"""Помощники для правил об оценочных формулировках.

Правило об оценке работает не по строке, а по предложению: «значительно» законно,
когда рядом названа величина, а перенос строки в исходнике границей фразы не
является. Поэтому здесь строки сначала собираются в абзац, а из абзаца берётся
предложение вокруг найденного слова.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила.
"""

import re
from collections.abc import Hashable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from nk.core.document import Document, Line
from nk.rules._shared import BIBLIOGRAPHY_ENVIRONMENT
from nk.rules._text import CODE_ENVIRONMENTS, prose

#: Окончания полного прилагательного с твёрдой основой: «современный», «простой».
HARD = "ый ой ого ому ым ом ая ую ое ые ых ыми"

#: То же после «г», «к», «х»: «гибкий», «плохой».
VELAR = "ий ой ого ому им ом ая ую ое ие их ими"

#: То же после шипящей: «хороший», «лучший».
SIBILANT = "ий его ему им ем ая ей ую ее ие их ими"

#: Название работы текстом отчёта не является: тема утверждена и оценку в ней
#: автор не выбирал.
TITLE_COMMAND = "title"

#: Опора на величину: число в самом предложении либо ссылка на объект, где
#: величина приведена. Аргументы ссылок из прозы вырезаны, имена команд — нет.
_MEASURE = re.compile(r"\d|\\(?:ref|eqref|autoref|cref|Cref|nameref)\b")

#: Граница предложения: точка с прописной буквой следом. Сокращение «см. таблицу»
#: предложения не заканчивает, иначе опора отрезалась бы от слова, к которому
#: она относится.
_SENTENCE_BREAK = re.compile(r"[.!?]\s+(?=[«(\"]?[А-ЯЁA-Z])")


@dataclass(frozen=True, slots=True)
class Mention:
    """Слово из перечня, найденное в тексте отчёта."""

    line: Line
    col: int
    found: str
    sentence: str
    """Предложение, в котором стоит слово: по нему судят об опоре на величину."""


def forms(stems: Mapping[str, str]) -> str:
    """Словоформы: основа и окончания, которые она принимает."""
    return " ".join(stem + ending for stem, endings in stems.items() for ending in endings.split())


def pattern(*groups: str) -> re.Pattern[str]:
    """Шаблон по перечням словоформ: слово целиком, без учёта регистра и «ё».

    Длинные формы идут первыми: иначе «хорош» совпал бы раньше «хорошего»
    и в сообщение попало бы полслова.
    """
    words = sorted({word for group in groups for word in group.split()}, key=len, reverse=True)
    body = "|".join(word.replace("ё", "[её]") for word in words)
    return re.compile(rf"\b(?:{body})\b", re.IGNORECASE)


def terms(*phrases: str) -> re.Pattern[str]:
    """Шаблон устойчивых сочетаний, в которых слово — часть термина.

    Пробел в сочетании считается любым: в прозе на месте вырезанной формулы или
    аргумента команды остаются пробелы, а перенос строки склеен пробелом.
    """
    return re.compile("|".join(phrase.replace(" ", r"\s+") for phrase in phrases), re.IGNORECASE)


def mentions(
    doc: Document,
    words: re.Pattern[str],
    *,
    exceptions: re.Pattern[str],
    allow: Iterable[str] = (),
    headings: bool = False,
) -> Iterator[Mention]:
    """Слова перечня в тексте отчёта, кроме терминов и разрешённых профилем.

    Листинги, формулы, список источников и, пока не сказано иное, рубрикация
    не проверяются: оценку там либо не автор выбирал, либо это не текст.
    """
    allowed = tuple(fold(item) for item in allow)
    for paragraph in _paragraphs(doc, headings=headings):
        text, offsets = _join(paragraph)
        skipped = [match.span() for match in exceptions.finditer(text)]
        for (line, line_text), offset in zip(paragraph, offsets, strict=True):
            for match in words.finditer(line_text):
                start = offset + match.start()
                if any(begin <= start < end for begin, end in skipped):
                    continue
                if fold(match.group()).startswith(allowed):
                    continue
                yield Mention(
                    line=line,
                    col=match.start() + 1,
                    found=match.group(),
                    sentence=_sentence(text, start),
                )


def has_measure(sentence: str) -> bool:
    """Названа ли в предложении величина: число или ссылка на объект с ним."""
    return _MEASURE.search(sentence) is not None


def fold(word: str) -> str:
    """Слово в виде, в котором его сравнивают: без регистра и без «ё»."""
    return word.casefold().replace("ё", "е")


def _paragraphs(doc: Document, *, headings: bool) -> Iterator[list[tuple[Line, str]]]:
    """Абзацы отчёта: подряд идущие строки прозы одного файла."""
    skipped = _skipped_lines(doc, headings=headings)
    paragraph: list[tuple[Line, str]] = []
    previous: Path | None = None
    for line in doc.iter_lines():
        dropped = line.is_blank or (line.path, line.lineno) in skipped
        if dropped or line.path != previous:
            if paragraph:
                yield paragraph
            paragraph = []
        previous = line.path
        if not dropped:
            paragraph.append((line, prose(doc, line)))
    if paragraph:
        yield paragraph


def _join(paragraph: list[tuple[Line, str]]) -> tuple[str, list[int]]:
    """Текст абзаца и позиция каждой строки в нём."""
    offsets: list[int] = []
    parts: list[str] = []
    length = 0
    for _, text in paragraph:
        offsets.append(length)
        parts.append(text)
        length += len(text) + 1
    return " ".join(parts), offsets


def _sentence(text: str, index: int) -> str:
    """Предложение абзаца, внутри которого стоит позиция ``index``.

    Границы ищутся по всему абзацу, а не по обрезанной подстроке: за границей
    поиска регулярное выражение не видит буквы, по которой узнаётся конец фразы.
    """
    start, end = 0, len(text)
    for match in _SENTENCE_BREAK.finditer(text):
        if match.end() <= index:
            start = match.end()
        elif match.start() >= index:
            end = match.start()
            break
    return text[start:end]


def _skipped_lines(doc: Document, *, headings: bool) -> frozenset[tuple[Path, int]]:
    key: Hashable = ("wording:skipped", headings)
    return doc.memo(key, lambda: _collect_skipped(doc, headings=headings))


def _collect_skipped(doc: Document, *, headings: bool) -> frozenset[tuple[Path, int]]:
    skipped = set(doc.structure.covered_lines(*CODE_ENVIRONMENTS, BIBLIOGRAPHY_ENVIRONMENT))
    if not headings:
        names = (*doc.headings.names, TITLE_COMMAND)
        skipped.update(
            (command.path, lineno)
            for command in doc.structure.find_commands(*names)
            for lineno in range(command.span.start, command.span.end + 1)
        )
    return frozenset(skipped)
