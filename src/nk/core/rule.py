"""Правило, декоратор регистрации и реестр.

Правило — чистая функция: ни ввода-вывода, ни состояния между вызовами, ни чтения
файлов помимо того, что уже в документе.
"""

import inspect
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from nk.core.categories import of_module
from nk.core.document import Document, Line, Span
from nk.core.finding import Finding, Fix, Severity
from nk.core.position import Region
from nk.core.profile import Params
from nk.core.standards import NO_CLAUSE, Standard


class RuleCallable(Protocol):
    """Функция правила до оборачивания декоратором."""

    __name__: str

    def __call__(self, doc: Document) -> Iterable[Finding]: ...


@runtime_checkable
class Rule(Protocol):
    """Контракт правила."""

    id: str
    clauses: Mapping[str, str]
    severity: Severity
    title: str

    def __call__(self, doc: Document) -> Iterable[Finding]: ...


class DuplicateRuleError(ValueError):
    """Два правила объявили один и тот же идентификатор."""


class UnknownRuleError(KeyError):
    """Запрошено правило, которого нет в реестре."""

    def __str__(self) -> str:
        # KeyError по умолчанию печатает repr аргумента, а сообщение уходит пользователю.
        return str(self.args[0]) if self.args else ""


@dataclass(frozen=True, slots=True)
class RuleImpl:
    """Правило, зарегистрированное декоратором :func:`rule`.

    Метод :meth:`finding` проставляет метаданные правила сам, чтобы автор не
    дублировал их из декоратора и не мог рассогласовать.
    """

    id: str
    severity: Severity
    title: str
    func: RuleCallable
    clauses: Mapping[str, str] = field(default_factory=dict)
    """Пункт требования в каждом стандарте, где оно записано; ключ — имя стандарта.

    Пусто — требование не записано ни в одном: типографика.
    """

    universal: bool = False
    """Требование действует под любым стандартом, а не только под названными в ``clauses``.

    Пункты отвечают, где требование записано, а не когда его проверять, и эти
    ответы расходятся: неразрывный пробел между числом и единицей нужен в любом
    отчёте, хотя пункт для него есть только у одного стандарта. Правило без
    пунктов — типографика — универсально само собой.
    """

    description: str = ""
    """Развёрнутое описание на Markdown: докстринг функции правила, источник страницы в документации."""
    default_params: Params = field(default_factory=dict)
    allow_missing_suggestion: bool = False
    """Разрешить находки без ``suggestion`` — только если исправление принципиально неоднозначно."""

    fixable: bool = False
    """Правило умеет чинить нарушение ключом ``--fix``. Проверяется на фикстурах."""

    default_off: bool = False
    """Правило включается только явно — профилем или ключом ``--select``."""

    deprecated_ids: tuple[str, ...] = ()
    """Прежние идентификаторы правила: они остаются рабочими в ключах, профилях
    и директивах подавления, чтобы переименование не ломало чужие исходники."""

    def __call__(self, doc: Document) -> Iterator[Finding]:
        yield from self.func(doc)

    @property
    def module(self) -> str:
        return getattr(self.func, "__module__", "<unknown>")

    @property
    def category(self) -> str:
        """Чем правило регулирует оформление: каталог, в котором оно лежит."""
        return of_module(self.module)

    def clause_for(self, standard_id: str) -> str:
        """Пункт требования в этом стандарте либо пустая строка."""
        return self.clauses.get(standard_id, NO_CLAUSE)

    def applies_under(self, standard: Standard) -> bool:
        """Проверяется ли требование, когда отчёт идёт по этому стандарту."""
        return self.universal or standard.id in self.clauses

    def params(self, doc: Document) -> Params:
        """Значения по умолчанию, перекрытые профилем документа."""
        return {**self.default_params, **doc.profile.params_for(self.id)}

    def finding(
        self,
        doc: Document,
        at: Line | Span,
        *,
        message: str,
        requirement: str,
        suggestion: str | None = None,
        col: int | None = None,
        fix: Region | Fix | None = None,
    ) -> Finding:
        """Собрать находку по позиции в документе.

        ``fix`` — регион, который целиком заменяется текстом ``suggestion``;
        так оформляется частый случай, когда ``suggestion`` и есть готовая
        замена. Если замена отличается от текста подсказки — например подсказка
        говорит «убрать двоеточие», а заменять нужно один символ на пустую
        строку, — передаётся готовый :class:`~nk.core.finding.Fix`.
        """
        lineno = at.lineno if isinstance(at, Line) else at.start
        excerpt, offset = doc.excerpt_at(at.path, lineno, col)
        clause, source = doc.profile.requirement(self.id, self.clauses)
        return Finding(
            rule_id=self.id,
            clause=clause,
            source=source,
            severity=doc.profile.severity_for(self.id, self.severity),
            message=message,
            requirement=requirement,
            path=at.path,
            lineno=lineno,
            col=col,
            excerpt=excerpt,
            excerpt_offset=offset,
            context=doc.context(at.path, lineno, col=col),
            suggestion=suggestion,
            fix=_fix(fix, suggestion),
        )


class RuleRegistry:
    """Реестр правил с запретом на молчаливую перезапись идентификаторов."""

    def __init__(self) -> None:
        self._rules: dict[str, RuleImpl] = {}
        self._aliases: dict[str, str] = {}

    def register(self, impl: RuleImpl) -> RuleImpl:
        """Добавить правило. Дубль идентификатора — ошибка, а не перезапись."""
        existing = self._rules.get(impl.id)
        if existing is not None:
            raise DuplicateRuleError(
                f"правило {impl.id!r} уже объявлено в {existing.module}, "
                f"повторное объявление в {impl.module}"
            )
        for old in impl.deprecated_ids:
            taken = self._rules.get(old) or self._rules.get(self._aliases.get(old, ""))
            if taken is not None:
                raise DuplicateRuleError(
                    f"прежний идентификатор {old!r} правила {impl.id!r} "
                    f"занят правилом {taken.id!r} из {taken.module}"
                )
            self._aliases[old] = impl.id
        self._rules[impl.id] = impl
        return impl

    @property
    def aliases(self) -> Mapping[str, str]:
        """Прежние идентификаторы и их нынешние имена."""
        return dict(self._aliases)

    def canonical(self, rule_id: str) -> str:
        """Нынешнее имя правила: прежний идентификатор разворачивается в него."""
        return self._aliases.get(rule_id, rule_id)

    def get(self, rule_id: str) -> RuleImpl:
        try:
            return self._rules[self.canonical(rule_id)]
        except KeyError:
            raise UnknownRuleError(rule_id) from None

    def all(self) -> tuple[RuleImpl, ...]:
        """Все правила, отсортированные по идентификатору."""
        return tuple(sorted(self._rules.values(), key=lambda impl: impl.id))

    def default_params(self) -> dict[str, Params]:
        return {
            impl.id: impl.default_params for impl in self._rules.values() if impl.default_params
        }

    def clear(self) -> None:
        self._rules.clear()
        self._aliases.clear()

    def __contains__(self, rule_id: object) -> bool:
        return rule_id in self._rules or rule_id in self._aliases

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self) -> Iterator[RuleImpl]:
        return iter(self.all())


#: Глобальный реестр, в который регистрируются правила из пакета ``nk.rules``.
REGISTRY = RuleRegistry()


def rule(
    *,
    id: str,
    severity: Severity,
    title: str,
    standards: Mapping[Standard, str] | None = None,
    universal: bool = False,
    params: Params | None = None,
    allow_missing_suggestion: bool = False,
    fixable: bool = False,
    default_off: bool = False,
    deprecated_ids: tuple[str, ...] = (),
    registry: RuleRegistry | None = None,
) -> Callable[[RuleCallable], RuleImpl]:
    """Объявить правило::

        @rule(
            id="G732-6.5.7-caption-dot",
            standards={G732: "6.5.7"},
            severity=Severity.ERROR,
            title="Подпись рисунка заканчивается точкой",
        )
        def figure_caption_dot(doc: Document) -> Iterable[Finding]:
            for line in doc.iter_lines():
                ...
                yield figure_caption_dot.finding(doc, line, message=..., requirement=...)

    Обращение к правилу по имени внутри его тела резолвится в момент вызова,
    когда декоратор уже отработал.

    ``standards`` говорит, где требование записано, ``universal`` — под какими
    стандартами его проверять. Правило без ``standards`` универсально само собой;
    ``universal=True`` при названных пунктах объявляет требование, которое нужно
    и там, где пункта под него нет.
    """

    def decorate(func: RuleCallable) -> RuleImpl:
        impl = RuleImpl(
            id=id,
            clauses={item.id: clause for item, clause in (standards or {}).items()},
            universal=universal or not standards,
            severity=severity,
            title=title,
            func=func,
            description=inspect.cleandoc(func.__doc__ or ""),
            default_params=params or {},
            allow_missing_suggestion=allow_missing_suggestion,
            fixable=fixable,
            default_off=default_off,
            deprecated_ids=deprecated_ids,
        )
        # Явное сравнение с None: пустой реестр ложен из-за __len__.
        target = REGISTRY if registry is None else registry
        return target.register(impl)

    return decorate


def _fix(fix: Region | Fix | None, suggestion: str | None) -> Fix | None:
    if fix is None or isinstance(fix, Fix):
        return fix
    if suggestion is None:
        raise ValueError("правка объявлена без suggestion: заменять регион нечем")
    return Fix(region=fix, replacement=suggestion)
