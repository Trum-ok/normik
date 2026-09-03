"""Правило, декоратор регистрации и реестр.

Правило — чистая функция: ни ввода-вывода, ни состояния между вызовами, ни чтения
файлов помимо того, что уже в документе.
"""

from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from nk.core.document import Document, Line, Span
from nk.core.finding import Finding, Severity
from nk.core.profile import Params


class RuleCallable(Protocol):
    """Функция правила до оборачивания декоратором."""

    __name__: str

    def __call__(self, doc: Document) -> Iterable[Finding]: ...


@runtime_checkable
class Rule(Protocol):
    """Контракт правила."""

    id: str
    clause: str
    severity: Severity
    title: str

    def __call__(self, doc: Document) -> Iterable[Finding]: ...


class DuplicateRuleError(ValueError):
    """Два правила объявили один и тот же идентификатор."""


class UnknownRuleError(KeyError):
    """Запрошено правило, которого нет в реестре."""


@dataclass(frozen=True, slots=True)
class RuleImpl:
    """Правило, зарегистрированное декоратором :func:`rule`.

    Метод :meth:`finding` проставляет метаданные правила сам, чтобы автор не
    дублировал их из декоратора и не мог рассогласовать.
    """

    id: str
    clause: str
    severity: Severity
    title: str
    func: RuleCallable
    default_params: Params = field(default_factory=dict)
    allow_missing_suggestion: bool = False
    """Разрешить находки без ``suggestion`` — только если исправление принципиально неоднозначно."""

    def __call__(self, doc: Document) -> Iterator[Finding]:
        yield from self.func(doc)

    @property
    def module(self) -> str:
        return getattr(self.func, "__module__", "<unknown>")

    def params(self, doc: Document) -> Mapping[str, object]:
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
    ) -> Finding:
        """Собрать находку по позиции в документе."""
        lineno = at.lineno if isinstance(at, Line) else at.start
        return Finding(
            rule_id=self.id,
            clause=self.clause,
            severity=doc.profile.severity_for(self.id, self.severity),
            message=message,
            requirement=requirement,
            path=at.path,
            lineno=lineno,
            col=col,
            excerpt=doc.excerpt(at.path, lineno),
            context=doc.context(at.path, lineno),
            suggestion=suggestion,
        )


class RuleRegistry:
    """Реестр правил с запретом на молчаливую перезапись идентификаторов."""

    def __init__(self) -> None:
        self._rules: dict[str, RuleImpl] = {}

    def register(self, impl: RuleImpl) -> RuleImpl:
        """Добавить правило. Дубль идентификатора — ошибка, а не перезапись."""
        existing = self._rules.get(impl.id)
        if existing is not None:
            raise DuplicateRuleError(
                f"правило {impl.id!r} уже объявлено в {existing.module}, "
                f"повторное объявление в {impl.module}"
            )
        self._rules[impl.id] = impl
        return impl

    def get(self, rule_id: str) -> RuleImpl:
        try:
            return self._rules[rule_id]
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

    def __contains__(self, rule_id: object) -> bool:
        return rule_id in self._rules

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self) -> Iterator[RuleImpl]:
        return iter(self.all())


#: Глобальный реестр, в который регистрируются правила из пакета ``nk.rules``.
REGISTRY = RuleRegistry()


def rule(
    *,
    id: str,
    clause: str,
    severity: Severity,
    title: str,
    params: Params | None = None,
    allow_missing_suggestion: bool = False,
    registry: RuleRegistry | None = None,
) -> Callable[[RuleCallable], RuleImpl]:
    """Объявить правило::

        @rule(
            id="G732-6.5.7-caption-dot",
            clause="6.5.7",
            severity=Severity.ERROR,
            title="Подпись рисунка заканчивается точкой",
        )
        def figure_caption_dot(doc: Document) -> Iterable[Finding]:
            for line in doc.iter_lines():
                ...
                yield figure_caption_dot.finding(doc, line, message=..., requirement=...)

    Обращение к правилу по имени внутри его тела резолвится в момент вызова,
    когда декоратор уже отработал.
    """

    def decorate(func: RuleCallable) -> RuleImpl:
        impl = RuleImpl(
            id=id,
            clause=clause,
            severity=severity,
            title=title,
            func=func,
            default_params=params or {},
            allow_missing_suggestion=allow_missing_suggestion,
        )
        # Явное сравнение с None: пустой реестр ложен из-за __len__.
        target = REGISTRY if registry is None else registry
        return target.register(impl)

    return decorate
