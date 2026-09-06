"""Категории правил: что именно правило регулирует.

Категория — это каталог, в котором лежит правило: правило из ``nk.rules.figures``
относится к иллюстрациям. Таксономия одна и держится файловой системой, поэтому
в объявлении правила категорию не повторяют, а положить файл мимо категории
нельзя — реестр такое правило не примет.

Категории не повторяют разделы стандарта: у разных стандартов разделы разные,
а иллюстрации остаются иллюстрациями.
"""

from dataclasses import dataclass

PACKAGE = "nk.rules"

#: Категория правила вне пакета правил — например объявленного в тесте.
NONE = ""


class UnknownCategoryError(ValueError):
    """Правило лежит в каталоге, который категорией не объявлен."""


@dataclass(frozen=True, slots=True)
class Category:
    name: str
    """Имя каталога в ``nk.rules``."""

    title: str
    """Заголовок раздела в документации и в перечне правил."""


#: Категории в порядке, в котором они идут в документации: сперва отчёт целиком,
#: затем его части, затем оформление текста.
CATEGORIES: tuple[Category, ...] = (
    Category("structure", "Структура отчёта"),
    Category("headings", "Заголовки и рубрикация"),
    Category("enumerations", "Перечисления"),
    Category("abstract", "Реферат"),
    Category("terms", "Термины и сокращения"),
    Category("figures", "Иллюстрации"),
    Category("tables", "Таблицы"),
    Category("formulas", "Формулы"),
    Category("notes", "Примечания и сноски"),
    Category("bibliography", "Источники и ссылки на них"),
    Category("appendices", "Приложения"),
    Category("text", "Изложение текста"),
    Category("typography", "Типографика"),
)

BY_NAME: dict[str, Category] = {category.name: category for category in CATEGORIES}


def of_module(module: str) -> str:
    """Категория по модулю правила. Вне пакета правил категории нет."""
    prefix = f"{PACKAGE}."
    if not module.startswith(prefix):
        return NONE
    return module[len(prefix) :].split(".")[0]


def title(name: str) -> str:
    try:
        return BY_NAME[name].title
    except KeyError:
        raise UnknownCategoryError(name) from None


def rank(name: str) -> int:
    """Место категории в порядке следования; неизвестная уходит в конец."""
    return next(
        (index for index, category in enumerate(CATEGORIES) if category.name == name),
        len(CATEGORIES),
    )
