"""Общие помощники правил.

Модуль начинается с подчёркивания, поэтому реестр не пытается собрать из него
правила. Правилам он доступен обычным импортом.
"""

import re
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

from nk.core.document import Command, Document, Environment, Line, Span
from nk.core.elements import canonical_element, normalize_element
from nk.core.finding import Finding, Fix
from nk.core.headings import PAGE_BREAK_COMMANDS, is_heading_call
from nk.core.numbering import Scheme
from nk.core.position import Region
from nk.core.rule import RuleImpl

FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*", "SCfigure", "wrapfigure"})
TABLE_ENVIRONMENTS = frozenset({"table", "table*", "longtable", "sidewaystable"})
TABULAR_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "longtable", "array"})
GRAPHIC_COMMANDS = frozenset({"includegraphics", "includesvg", "input", "includepdf"})
GRAPHIC_ENVIRONMENTS = frozenset({"tikzpicture", "pgfpicture", "picture"})

#: Знаки, которые правила ставят в исходник вместо неверных.
DASH = "—"
NBSP = "~"

CAPTION_COMMANDS = frozenset({"caption", "caption*", "captionof"})
LABEL_COMMANDS = frozenset({"label"})
REF_COMMANDS = frozenset({"ref", "eqref", "autoref", "cref", "Cref", "pageref", "nameref", "vref"})
CITE_COMMANDS = frozenset({"cite", "citep", "citet", "citealp", "citeauthor", "nocite"})

_COMMAND = re.compile(r"\\[A-Za-z]+\*?")
_BRACES = re.compile(r"[{}$~]")
_LABEL = re.compile(r"\\label\s*\{[^{}]*\}")


def captions(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in CAPTION_COMMANDS:
            yield command


def labels(environment: Environment) -> Iterator[Command]:
    for command in environment.all_commands():
        if command.name in LABEL_COMMANDS:
            yield command


def caption_text(command: Command) -> str:
    """Текст наименования без меток.

    ``\\label`` внутри подписи — распространённая форма, и проверять точку или
    регистр надо по самому тексту, а не по хвосту с меткой.
    """
    return _LABEL.sub("", _caption_argument(command)).strip()


def caption_labels(command: Command) -> tuple[str, ...]:
    """Метки, записанные внутри подписи, как есть."""
    return tuple(_LABEL.findall(_caption_argument(command)))


def render_caption(command: Command, text: str) -> str:
    """Команда подписи с новым текстом наименования.

    Тип объекта у ``\\captionof``, краткая форма в квадратных скобках и метки
    внутри подписи сохраняются: правка меняет только текст.
    """
    parts = [f"\\{command.name}"]
    if command.name == "captionof" and command.args:
        parts.append(f"{{{command.args[0]}}}")
    parts.extend(f"[{option}]" for option in command.options)
    parts.append("{" + text + "".join(caption_labels(command)) + "}")
    return "".join(parts)


def _caption_argument(command: Command) -> str:
    """Аргумент с наименованием: у ``\\captionof`` первый аргумент — тип объекта."""
    args = command.args
    if command.name == "captionof" and len(args) > 1:
        return args[1]
    return args[0] if args else ""


def caption_findings(
    impl: RuleImpl,
    doc: Document,
    environments: frozenset[str],
    *,
    requirement: str,
    check: Callable[[str], tuple[str, str] | None],
) -> Iterator[Finding]:
    """Находки по наименованиям объектов.

    Правила о наименовании различаются только проверкой текста: обход окружений,
    сборка новой подписи и границы правки у них общие. ``check`` получает текст
    наименования и возвращает сообщение вместе с исправленным текстом либо
    ``None``, если нарушения нет.
    """
    for environment in doc.structure.find_environments(*environments):
        for command in captions(environment):
            found = check(caption_text(command))
            if found is None:
                continue
            message, corrected = found
            yield impl.finding(
                doc,
                command.span,
                message=message,
                requirement=requirement,
                suggestion=render_caption(command, corrected),
                col=command.col,
                fix=command.region,
            )


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


def first_outside_reference(
    doc: Document, environment: Environment, keys: Iterable[str]
) -> Command | None:
    """Первая ссылка на объект в порядке отчёта, не считая ссылок внутри него самого."""
    wanted = set(keys)
    for command in ordered_commands(doc, *REF_COMMANDS):
        if command.path == environment.path and environment.span.contains(command.lineno):
            continue
        for arg in command.args:
            if any(key.strip() in wanted for key in arg.split(",")):
                return command
    return None


def is_below(doc: Document, command: Command, span: Span) -> bool:
    """Стоит ли команда ниже диапазона по порядку отчёта, а не по алфавиту файлов."""
    return (doc.file_index(command.path), command.lineno) > (doc.file_index(span.path), span.end)


def place(command: Command, span: Span) -> str:
    """Место команды для сообщения: файл указывается, только если он другой."""
    if command.path == span.path:
        return f"строка {command.lineno}"
    return f"{command.path.name}, строка {command.lineno}"


def float_position(
    impl: RuleImpl,
    doc: Document,
    environments: frozenset[str],
    *,
    message: Callable[[str, str], str],
    requirement: str,
) -> Iterator[Finding]:
    """Объекты, целиком стоящие выше первой ссылки на них.

    Объект без метки пропускается: о нём сообщает правило о ссылках.
    ``message`` получает метку объекта и место ссылки.
    """
    for environment in doc.structure.find_environments(*environments):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            continue
        reference = first_outside_reference(doc, environment, keys)
        if reference is None or not is_below(doc, reference, environment.span):
            continue
        yield impl.finding(
            doc,
            environment.span,
            message=message(keys[0], place(reference, environment.span)),
            requirement=requirement,
            suggestion=(
                f"Перенести окружение {environment.name} ниже абзаца со ссылкой "
                f"(строка {reference.lineno})."
            ),
        )


def float_no_reference(
    impl: RuleImpl,
    doc: Document,
    environments: frozenset[str],
    *,
    requirement: str,
    unlabelled: str,
    unlabelled_suggestion: str,
    missing: Callable[[str], str],
    missing_suggestion: Callable[[str], str],
) -> Iterator[Finding]:
    """Объекты, на которые в тексте не сослались.

    Объект без метки — та же находка: сослаться на него нечем. ``missing``
    и ``missing_suggestion`` получают метку объекта.
    """
    referenced = referenced_labels(doc)
    for environment in doc.structure.find_environments(*environments):
        keys = [command.arg for command in labels(environment) if command.arg]
        if not keys:
            yield impl.finding(
                doc,
                environment.span,
                message=unlabelled,
                requirement=requirement,
                suggestion=unlabelled_suggestion,
            )
            continue
        if any(key in referenced for key in keys):
            continue
        yield impl.finding(
            doc,
            environment.span,
            message=missing(keys[0]),
            requirement=requirement,
            suggestion=missing_suggestion(keys[0]),
        )


def reference_abbreviation(
    impl: RuleImpl,
    doc: Document,
    pattern: re.Pattern[str],
    *,
    message: str,
    requirement: str,
    suggestion: str,
) -> Iterator[Finding]:
    """Сокращение вместо полного слова в ссылке на объект.

    Сообщают об одной находке на строку: сокращение в ссылке правят по всему
    абзацу разом, и второй указатель на той же строке ничего не добавляет.
    """
    for line in doc.iter_lines():
        match = pattern.search(line.stripped)
        if match is None:
            continue
        yield impl.finding(
            doc,
            line,
            message=message,
            requirement=requirement,
            suggestion=suggestion,
            col=match.start() + 1,
        )


#: Точка переноса, заданная в исходнике вручную.
HYPHENATION_MARKER = "\\-"


def without_hyphenation(doc: Document, command: Command) -> Fix | None:
    """Тот же фрагмент исходника, но без точек переноса."""
    if command.region is None:
        return None
    return Fix(
        region=command.region,
        replacement=doc.slice(command.region).replace(HYPHENATION_MARKER, ""),
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


def appendix_numbering(
    impl: RuleImpl, doc: Document, kind: str, requirement: str
) -> Iterator[Finding]:
    """Объекты приложения, пронумерованные сквозной нумерацией основной части.

    Требование одно и то же для иллюстраций, таблиц и формул, а счётчик LaTeX
    называется так же, как сам вид объекта.
    """
    for item in doc.numbering.by_kind(kind):
        if not item.in_appendix or item.scheme is Scheme.BY_SECTION:
            continue
        yield impl.finding(
            doc,
            item.span,
            message=(
                f"{item.title} находится в приложении {item.appendix}, "
                f"но нумеруется сквозной нумерацией основной части."
            ),
            requirement=requirement,
            suggestion=(
                f"Добавить в преамбулу \\counterwithin{{{kind}}}{{section}}: "
                f"тогда номер станет {item.appendix}.1 и далее."
            ),
        )


def headings(doc: Document) -> Iterator[Command]:
    """Команды рубрикации, включая макросы шаблона кафедры."""
    for command in doc.structure.find_commands(*doc.headings.names):
        if is_heading_call(command):
            yield command


def ordered_headings(doc: Document) -> list[Command]:
    """Команды рубрикации в порядке следования по отчёту."""
    return list(
        doc.memo(
            "ordered_headings",
            lambda: tuple(
                command
                for command in ordered_commands(doc, *doc.headings.names)
                if is_heading_call(command)
            ),
        )
    )


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


BIBLIOGRAPHY_ENVIRONMENT = "thebibliography"
BIBITEM_COMMAND = "bibitem"
BIBTEX_COMMANDS = frozenset({"bibliography", "addbibresource", "printbibliography"})


def ordered_commands(doc: Document, *names: str) -> list[Command]:
    """Команды с этими именами в порядке следования по отчёту."""
    wanted = frozenset(names)
    return [command for command in doc.ordered_commands() if command.name in wanted]


def is_numbered_environment(name: str) -> bool:
    """Нумеруется ли формула: окружение без звёздочки."""
    return not name.endswith("*") and name != "displaymath"


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
    same_file = doc.memo(
        ("heading_lines", command.path),
        lambda: sorted(item.lineno for item in ordered_headings(doc) if item.path == command.path),
    )
    following = [lineno for lineno in same_file if lineno > command.span.end]
    end = following[0] - 1 if following else len(doc.lines_of(command.path))
    return [line for line in doc.lines_of(command.path) if command.span.end < line.lineno <= end]


#: «45 с.», «3 рис.», «12 источн.» — элементы сведений об объёме отчёта.
VOLUME_ITEM = re.compile(r"\d+\s*~?\s*(?:с|кн|рис|табл|источн|прил|ил)\.")

KEYWORDS_PREFIX = re.compile(r"^\s*(?:\\\w+\{)?\s*КЛЮЧЕВЫЕ\s+СЛОВА\s*:", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class KeywordList:
    """Перечень ключевых слов: строки исходника, слова и начало перечня."""

    lines: tuple[Line, ...]
    words: tuple[str, ...]
    col: int
    """Колонка, с которой перечень начинается в первой строке."""

    @property
    def line(self) -> Line:
        return self.lines[0]

    @property
    def inline(self) -> str | None:
        """Текст перечня, если он уложен в одну строку исходника.

        У перечня, разорванного на несколько строк, между ними могут стоять
        комментарии: заменять такой фрагмент целиком нельзя.
        """
        if len(self.lines) > 1:
            return None
        return self.line.stripped[self.col - 1 :].rstrip()


def keyword_lists(doc: Document) -> Iterator[KeywordList]:
    """Перечни ключевых слов документа.

    Перечень приводят в строку через запятые, поэтому берётся одна строка исходника
    вместе с продолжением до первой пустой строки.
    """
    lines = list(doc.iter_lines())
    for index, line in enumerate(lines):
        match = KEYWORDS_PREFIX.match(line.stripped)
        if match is None:
            continue
        own = [line]
        parts = [line.stripped[match.end() :]]
        for following in lines[index + 1 :]:
            if following.path != line.path or following.is_blank:
                break
            own.append(following)
            parts.append(following.stripped)
        text = visible_text(" ".join(parts))
        yield KeywordList(
            lines=tuple(own),
            words=tuple(word.strip() for word in text.split(",") if word.strip()),
            col=match.end() + 1,
        )


#: Термин и его определение разделяют тире; дефис на этом месте разбирают
#: правила 6.14 и 6.15, порядку записей он не мешает.
LISTING_SEPARATOR = re.compile(r"\s+[—–-]\s+")


def listing_entries(doc: Document, elements: frozenset[str]) -> Iterator[tuple[Line, str]]:
    """Записи перечня терминов или сокращений: строка и её левая часть.

    Вводная фраза перечня разделителя не содержит и записью не считается.
    """
    for command, element in structural_headings(doc):
        if element not in elements:
            continue
        for line in section_lines(doc, command):
            text = visible_text(line.stripped).strip()
            match = LISTING_SEPARATOR.search(text)
            if match is None:
                continue
            left = text[: match.start()].strip()
            if left:
                yield line, left


#: Дефис между пробелами на месте тире: «СИ - система измерений».
_LISTING_HYPHEN = re.compile(r"\S( - )\S")


def listing_dash(
    impl: RuleImpl, doc: Document, elements: frozenset[str], requirement: str
) -> Iterator[Finding]:
    """Дефис вместо тире в записях перечня."""
    for command, element in structural_headings(doc):
        if element not in elements:
            continue
        for line in section_lines(doc, command):
            match = _LISTING_HYPHEN.search(line.stripped)
            if match is None:
                continue
            start, end = match.span(1)
            yield impl.finding(
                doc,
                line,
                message="Расшифровка отделена дефисом, а не тире.",
                requirement=requirement,
                suggestion=f"Заменить дефис на тире: {DASH}",
                col=start + 2,
                fix=Fix(Region.in_line(line.path, line.lineno, start + 2, end), DASH),
            )


ITEM_COMMAND = "item"

#: Обозначение элемента перечисления: буква или число, за которыми может стоять
#: скобка или точка.
_ENUMERATION_LABEL = re.compile(r"^\s*(?P<mark>[A-Za-zА-Яа-яЁё]|\d+)\s*(?P<tail>[).]?)\s*$")


def parse_enumeration_label(option: str) -> tuple[str, str] | None:
    """Обозначение и знак после него либо ``None``, если это не обозначение.

    Форму обозначения разбирают два правила пункта 6.4.6 — одно проверяет саму
    форму, другое допустимость буквы, — и разбирают одинаково.
    """
    match = _ENUMERATION_LABEL.match(option.strip())
    if match is None:
        return None
    return match.group("mark"), match.group("tail")


def alphabet_key(text: str) -> str:
    """Ключ сравнения по алфавиту: регистр не различается, «ё» идёт вместе с «е»."""
    return text.casefold().replace("ё", "е")


def alphabet_of(text: str) -> str:
    """Алфавит первой буквы записи: перечень с латинскими сокращениями ведут отдельно."""
    for char in text.casefold():
        if char.isalpha():
            return "latin" if char.isascii() else "cyrillic"
    return ""


def listing_order(
    impl: RuleImpl, doc: Document, elements: frozenset[str], *, noun: str, requirement: str
) -> Iterator[Finding]:
    """Записи перечня, нарушающие алфавитный порядок.

    Сравнивается только соседняя пара: запись сопоставляется с предыдущей, а не
    со всем перечнем, — иначе одна переставленная запись обвиняла бы весь хвост.
    """
    previous = ""
    previous_key = ""
    previous_alphabet = ""
    for line, entry in listing_entries(doc, elements):
        key, alphabet = alphabet_key(entry), alphabet_of(entry)
        if alphabet != previous_alphabet or key >= previous_key:
            previous, previous_key, previous_alphabet = entry, key, alphabet
            continue
        yield impl.finding(
            doc,
            line,
            message=f"{noun} «{entry}» стоит после «{previous}», хотя по алфавиту идёт раньше.",
            requirement=requirement,
            suggestion=f"Переставить запись «{entry}» выше записи «{previous}».",
        )
        previous, previous_key, previous_alphabet = entry, key, alphabet


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
#: «в приложении А», «см. приложение~Б» — упоминание приложения в тексте.
APPENDIX_REFERENCE = re.compile(r"приложени\w*\s*~?\s*([А-Я])\b")
SECTION_LEVEL = 1

#: Команды разрыва страницы в том виде, в каком они встречаются в строке.
PAGE_BREAKS = tuple(f"\\{name}" for name in sorted(PAGE_BREAK_COMMANDS))
PAGE_BREAK = "\\newpage"


def previous_content(doc: Document, command: Command) -> str | None:
    """Ближайшая непустая строка выше команды либо ``None``, если её нет.

    Рубрика в начале файла даёт ``None``: то, что стоит перед ней, осталось
    в файле, который её включает.
    """
    for lineno in range(command.lineno - 1, 0, -1):
        line = doc.line_at(command.path, lineno)
        if line is not None and not line.is_blank:
            return line.stripped.lstrip()
    return None


def starts_page(previous: str) -> bool:
    """Начинает ли рубрика после этой строки новую страницу.

    Разрыв считается только последним на строке: после «\\newpage Текст»
    рубрика идёт уже за текстом, то есть посреди страницы.
    """
    return any(previous.rstrip().endswith(mark) for mark in PAGE_BREAKS)


def leading_text(doc: Document, command: Command) -> str:
    """Текст слева от команды в её строке.

    Он печатается перед рубрикой, поэтому разрыв страницы выше по файлу
    рубрику уже не открывает: разрыв нужен между этим текстом и ею.
    """
    line = doc.line_at(command.path, command.lineno)
    return "" if line is None else line.stripped[: command.col - 1].strip()


def page_break_fix(doc: Document, command: Command) -> Fix:
    """Правка, вставляющая разрыв страницы вплотную перед рубрикой.

    Рубрика посреди строки получает разрыв там же, где стоит сама: вставка
    в начало строки унесла бы на новую страницу и хвост предыдущего абзаца.
    """
    col = command.col if leading_text(doc, command) else 1
    return Fix(Region.at(command.path, command.lineno, col), f"{PAGE_BREAK}\n")


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
