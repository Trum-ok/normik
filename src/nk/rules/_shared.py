"""Общие помощники правил.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила. Правилам он доступен обычным импортом.
"""

import re
from collections.abc import Iterator

from nk.core.document import Command, Document, Environment, Line, Span
from nk.core.elements import canonical_element, normalize_element

FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*", "SCfigure", "wrapfigure"})
TABLE_ENVIRONMENTS = frozenset({"table", "table*", "longtable", "sidewaystable"})
TABULAR_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "longtable", "array"})
GRAPHIC_COMMANDS = frozenset({"includegraphics", "includesvg", "input", "includepdf"})
GRAPHIC_ENVIRONMENTS = frozenset({"tikzpicture", "pgfpicture", "picture"})

CAPTION_COMMANDS = frozenset({"caption", "caption*", "captionof"})
LABEL_COMMANDS = frozenset({"label"})
REF_COMMANDS = frozenset({"ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref", "vref"})
CITE_COMMANDS = frozenset({"cite", "citep", "citet", "citealp", "citeauthor", "nocite"})

_COMMAND = re.compile(r"\\[A-Za-z]+\*?")
_BRACES = re.compile(r"[{}$~]")


def captions(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in CAPTION_COMMANDS:
            yield command


def labels(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in LABEL_COMMANDS:
            yield command


def caption_text(command: Command) -> str:
    """Текст наименования: у ``\\captionof`` первый аргумент — тип плавающего объекта."""
    args = command.args
    if command.name == "captionof" and len(args) > 1:
        return args[1].strip()
    return args[0].strip() if args else ""


def referenced_labels(doc: Document) -> set[str]:
    """Метки, на которые в документе есть ссылка."""
    found: set[str] = set()
    for command in doc.structure.find_commands(*REF_COMMANDS):
        for arg in command.args:
            found.update(key.strip() for key in arg.split(",") if key.strip())
    return found


def cited_keys(doc: Document) -> set[str]:
    """Ключи источников, процитированные в тексте."""
    found: set[str] = set()
    for command in doc.structure.find_commands(*CITE_COMMANDS):
        for arg in command.args:
            found.update(key.strip() for key in arg.split(",") if key.strip())
    return found


def one_line(text: str) -> str:
    """Свернуть текст в одну строку: в LaTeX перевод строки внутри группы — пробел."""
    return " ".join(text.split())


def visible_text(text: str) -> str:
    """Текст без команд и служебных символов — для проверок регистра и содержания."""
    return one_line(_BRACES.sub(" ", _COMMAND.sub(" ", text)))


def first_letter(text: str) -> str:
    """Первая буква видимого текста либо пустая строка."""
    for char in visible_text(text):
        if char.isalpha():
            return char
    return ""


def has_graphic(environment: Environment) -> bool:
    return any(command.name in GRAPHIC_COMMANDS for command in environment.all_commands()) or any(
        child.name in GRAPHIC_ENVIRONMENTS for child in environment.walk()
    )


def first_graphic_line(environment: Environment) -> int | None:
    """Номер строки, с которой начинается изображение."""
    candidates = [
        command.lineno for command in environment.all_commands() if command.name in GRAPHIC_COMMANDS
    ]
    candidates.extend(
        child.span.start for child in environment.walk() if child.name in GRAPHIC_ENVIRONMENTS
    )
    return min(candidates) if candidates else None


def first_tabular_line(environment: Environment) -> int | None:
    """Номер строки, с которой начинается сама таблица."""
    starts = [
        child.span.start for child in environment.walk() if child.name in TABULAR_ENVIRONMENTS
    ]
    return min(starts) if starts else None


def headings(doc: Document) -> Iterator[Command]:
    """Команды рубрикации, включая макросы шаблона кафедры."""
    yield from doc.structure.find_commands(*doc.headings.names)


def ordered_headings(doc: Document) -> list[Command]:
    """Команды рубрикации в порядке следования по отчёту."""
    return ordered_commands(doc, *doc.headings.names)


def heading_level(doc: Document, command: Command) -> int:
    """Уровень рубрики: раздел, подраздел, пункт, подпункт."""
    return doc.headings.depth_of(command.name)


def heading_text(command: Command) -> str:
    return command.arg.strip()


def normalize_heading(text: str) -> str:
    """Заголовок без команд, знаков препинания и различий в регистре."""
    return normalize_element(visible_text(text))


def structural_element(doc: Document, text: str) -> str | None:
    """Каноническое наименование структурного элемента либо ``None``.

    Наименования, принятые кафедрой вместо стандартных, задаёт профиль.
    """
    return canonical_element(normalize_heading(text), doc.profile.element_aliases)


def is_numbered(doc: Document, command: Command) -> bool:
    """Нумеруется ли рубрика: команда без звёздочки, включая ту, что стоит за макросом."""
    return doc.headings.is_numbered(command.name)


#: Окружения выключных формул.
MATH_ENVIRONMENTS = frozenset(
    {
        "equation",
        "equation*",
        "align",
        "align*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "displaymath",
        "eqnarray",
        "eqnarray*",
        "alignat",
        "alignat*",
        "flalign",
        "flalign*",
    }
)

BIBLIOGRAPHY_ENVIRONMENT = "thebibliography"
BIBITEM_COMMAND = "bibitem"
BIBTEX_COMMANDS = frozenset({"bibliography", "addbibresource", "printbibliography"})


def ordered_commands(doc: Document, *names: str) -> list[Command]:
    """Команды в порядке следования по отчёту, а не по дереву окружений.

    Файлы упорядочены разворачиванием ``\\input`` и ``\\include``: порядок отчёта
    задаёт главный файл, а не алфавит имён включаемых.
    """
    return sorted(
        doc.structure.find_commands(*names),
        key=lambda command: (doc.file_index(command.path), command.lineno, command.col),
    )


def is_numbered_environment(name: str) -> bool:
    """Нумеруется ли формула: окружение без звёздочки."""
    return not name.endswith("*") and name != "displaymath"


#: Прописные буквы кириллицы, которыми обозначают приложения.
APPENDIX_LETTERS = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ"

DOCUMENT_ENVIRONMENT = "document"
CONTENTS_COMMAND = "tableofcontents"


def is_full_document(doc: Document) -> bool:
    """Проверяется отчёт целиком, а не отдельная глава.

    Правила о составе и порядке структурных элементов на отдельной главе
    выдавали бы сплошной шум.
    """
    return any(doc.structure.find_environments(DOCUMENT_ENVIRONMENT))


def structural_headings(doc: Document) -> list[tuple[Command, str]]:
    """Заголовки структурных элементов в порядке следования, с каноническим наименованием."""
    found: list[tuple[Command, str]] = []
    for command in ordered_headings(doc):
        element = structural_element(doc, heading_text(command))
        if element is not None:
            found.append((command, element))
    return found


def section_lines(doc: Document, command: Command) -> list[Line]:
    """Строки раздела: от заголовка до следующего заголовка в том же файле."""
    same_file = sorted(item.lineno for item in ordered_headings(doc) if item.path == command.path)
    following = [lineno for lineno in same_file if lineno > command.span.end]
    end = following[0] - 1 if following else len(doc.lines_of(command.path))
    return [line for line in doc.lines_of(command.path) if command.span.end < line.lineno <= end]


KEYWORDS_PREFIX = re.compile(r"^\s*(?:\\\w+\{)?\s*КЛЮЧЕВЫЕ\s+СЛОВА\s*:", re.IGNORECASE)


def keyword_lists(doc: Document) -> Iterator[tuple[Line, list[str]]]:
    """Строки перечня ключевых слов и сами слова.

    Перечень приводят в строку через запятые, поэтому берётся одна строка исходника
    вместе с продолжением до первой пустой строки.
    """
    lines = list(doc.iter_lines())
    for index, line in enumerate(lines):
        match = KEYWORDS_PREFIX.match(line.stripped)
        if match is None:
            continue
        parts = [line.stripped[match.end() :]]
        for following in lines[index + 1 :]:
            if following.path != line.path or following.is_blank:
                break
            parts.append(following.stripped)
        text = visible_text(" ".join(parts))
        yield line, [word.strip() for word in text.split(",") if word.strip()]


def capitalize_first(text: str) -> str:
    """Поднять первую видимую букву в регистре, пропуская имена команд."""
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 1
            while index < len(text) and text[index].isalpha():
                index += 1
            continue
        if char.isalpha():
            return text[:index] + char.upper() + text[index + 1 :]
        index += 1
    return text


APPENDIX_DESIGNATION = re.compile(r"^ПРИЛОЖЕНИЕ\s+(\S+)")
SECTION_LEVEL = 1


def appendix_spans(doc: Document) -> list[tuple[Command, str, Span]]:
    """Заголовки приложений с обозначением и диапазоном строк каждого.

    Приложение тянется до следующей рубрики уровня раздела в том же файле
    либо до конца файла.
    """
    sections = ordered_headings(doc)
    found: list[tuple[Command, str, Span]] = []
    for index, command in enumerate(sections):
        match = APPENDIX_DESIGNATION.match(normalize_heading(heading_text(command)))
        if match is None:
            continue
        end = len(doc.lines_of(command.path))
        for following in sections[index + 1 :]:
            if following.path != command.path:
                break
            if heading_level(doc, following) <= SECTION_LEVEL:
                end = following.lineno - 1
                break
        found.append((command, match.group(1), Span(command.path, command.span.start, end)))
    return found
