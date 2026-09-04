"""Команды CLI. Вся логика — в ядре; здесь только разбор аргументов и вывод."""

import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nk import __version__
from nk.core.baseline import Baseline, BaselineError
from nk.core.diagnostics import INTERNAL
from nk.core.finding import Severity
from nk.core.fixer import diff, plan, write
from nk.core.profile import Profile, ProfileError, load_profile
from nk.core.registry import load_rules, partition_ids, select_rules, validate_profile
from nk.core.rule import RuleImpl, UnknownRuleError
from nk.core.runner import RunResult, run
from nk.parse.tex import parse, parse_findings
from nk.report import agent, examples, human, rules_docs
from nk.report import json as json_report

app = typer.Typer(
    name="nk",
    help="Линтер оформления отчёта о НИР по ГОСТ 7.32-2017 для исходников LaTeX.",
    no_args_is_help=True,
    add_completion=False,
)
rules_app = typer.Typer(name="rules", help="Сведения о правилах.", no_args_is_help=True)
profile_app = typer.Typer(name="profile", help="Сведения о профилях.", no_args_is_help=True)
app.add_typer(rules_app)
app.add_typer(profile_app)

console = Console()
err_console = Console(stderr=True)

EXIT_OK = 0
EXIT_FOUND_ERRORS = 1
EXIT_INTERNAL_ERROR = 2

#: Сколько раз перепроверять исходники, применяя найденные правки.
FIX_PASSES = 5


class OutputFormat(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    JSON = "json"


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", help="Показать версию и выйти."),
) -> None:
    if version:
        console.print(f"nk {__version__}")
        raise typer.Exit()


@rules_app.command("list")
def rules_list() -> None:
    """Перечень правил: идентификатор, пункт стандарта, уровень, название."""
    registry = load_rules()
    if not len(registry):
        console.print("Правил пока нет.")
        return

    table = Table(box=None, pad_edge=False)
    table.add_column("ID")
    table.add_column("Пункт")
    table.add_column("Уровень")
    table.add_column("Название")
    for impl in registry:
        table.add_row(impl.id, impl.clause, impl.severity.value, impl.title)
    console.print(table)


@rules_app.command("show")
def rules_show(rule_id: str = typer.Argument(..., help="Идентификатор правила.")) -> None:
    """Подробности по правилу."""
    registry = load_rules()
    try:
        impl = registry.get(rule_id)
    except UnknownRuleError:
        err_console.print(f"Неизвестное правило: {rule_id}")
        raise typer.Exit(EXIT_INTERNAL_ERROR) from None

    console.print(f"[bold]{impl.id}[/bold] — {impl.title}")
    console.print(f"Пункт ГОСТ 7.32-2017: {impl.clause}")
    console.print(f"Уровень по умолчанию: {impl.severity.value}")
    console.print(f"Объявлено в: {impl.module}")
    if impl.description:
        console.print("")
        console.print(impl.description)
        console.print("")
    if impl.default_params:
        console.print("Параметры по умолчанию:")
        for name, value in sorted(impl.default_params.items()):
            console.print(f"  {name} = {value!r}")


@profile_app.command("show")
def profile_show(
    profile_source: str = typer.Option(
        None, "--profile", "-p", help="Имя встроенного профиля либо путь к TOML."
    ),
) -> None:
    """Итоговый набор правил после применения профиля."""
    registry = load_rules()
    try:
        profile = load_profile(profile_source)
        validate_profile(profile, registry)
    except ProfileError as error:
        err_console.print(f"Профиль: {error}")
        raise typer.Exit(EXIT_INTERNAL_ERROR) from None

    profile = profile.resolve(registry.default_params())
    active = {impl.id for impl in select_rules(registry, profile=profile)}

    console.print(f"Профиль: [bold]{profile.name}[/bold]")
    console.print(f"Правил включено: {len(active)} из {len(registry)}")
    if not len(registry):
        return

    table = Table(box=None, pad_edge=False)
    table.add_column("ID")
    table.add_column("Уровень")
    table.add_column("Состояние")
    table.add_column("Параметры")
    for impl in registry:
        severity = profile.severity_for(impl.id, impl.severity)
        changed = "" if severity is impl.severity else f" (было {impl.severity.value})"
        params = profile.params_for(impl.id)
        table.add_row(
            impl.id,
            f"{severity.value}{changed}",
            "включено" if impl.id in active else "отключено",
            ", ".join(f"{k}={v!r}" for k, v in sorted(params.items())),
        )
    console.print(table)


@app.command("check")
def check(
    paths: list[Path] = typer.Argument(..., help="Файлы или каталоги с исходниками .tex."),
    profile_source: str = typer.Option(
        None, "--profile", "-p", help="Имя встроенного профиля либо путь к TOML."
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.HUMAN, "--format", "-f", help="Формат вывода."
    ),
    select: str = typer.Option(
        None, "--select", help="Запустить только эти правила, через запятую."
    ),
    ignore: str = typer.Option(None, "--ignore", help="Исключить эти правила, через запятую."),
    severity: Severity = typer.Option(
        Severity.INFO, "--severity", help="Не показывать находки ниже уровня."
    ),
    limit: int = typer.Option(
        agent.DEFAULT_LIMIT, "--limit", help="Предел числа находок в выводе; 0 — без предела."
    ),
    fix: bool = typer.Option(False, "--fix", help="Применить правки к исходникам."),
    show_diff: bool = typer.Option(
        False, "--diff", help="Показать правки как diff, ничего не записывая."
    ),
    baseline_path: Path = typer.Option(
        None, "--baseline", help="Снимок известных нарушений: показывать только новые."
    ),
    write_baseline: Path = typer.Option(
        None, "--write-baseline", help="Записать снимок текущих находок и выйти."
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Только код возврата."),
) -> None:
    """Проверить исходники отчёта на соответствие ГОСТ 7.32-2017."""
    missing = [path for path in paths if not path.exists()]
    if missing:
        err_console.print("Не найдено: " + ", ".join(str(path) for path in missing))
        raise typer.Exit(EXIT_INTERNAL_ERROR)

    registry = load_rules()
    try:
        profile = load_profile(profile_source)
        validate_profile(profile, registry)
        selected_rules, _ = partition_ids(_split(select))
        ignored_rules, ignored_internal = partition_ids(_split(ignore))
        rules = select_rules(
            registry,
            profile=profile,
            select=selected_rules,
            ignore=ignored_rules,
        )
        baseline = Baseline.load(baseline_path) if baseline_path is not None else None
    except (ProfileError, UnknownRuleError, BaselineError) as error:
        err_console.print(str(error))
        raise typer.Exit(EXIT_INTERNAL_ERROR) from None

    check_run = _Check(
        paths=paths,
        rules=rules,
        profile=profile.resolve(registry.default_params()),
        baseline=baseline,
        ignored=ignored_internal | (profile.disabled & frozenset(INTERNAL)),
        known_ids=frozenset(impl.id for impl in registry) | frozenset(INTERNAL),
        # Снимок фиксируется по всем находкам: иначе его содержимое зависело бы
        # от ключа --severity, с которым его записали.
        threshold=Severity.INFO if write_baseline is not None else severity,
    )
    result = check_run()

    # Упавшее правило — внутренняя ошибка: часть проверок не выполнилась,
    # и зелёный прогон в CI говорил бы неправду. Снимок с пропущенными
    # проверками не записывается: он скрыл бы их находки навсегда.
    if write_baseline is not None:
        if result.failed_rules:
            _report_failures(result)
            raise typer.Exit(EXIT_INTERNAL_ERROR)
        _write_baseline(write_baseline, result)
        raise typer.Exit(EXIT_OK)

    if show_diff:
        sys.stdout.write(_diff(check_run, result))
        _report_failures(result)
        raise typer.Exit(EXIT_INTERNAL_ERROR if result.failed_rules else EXIT_OK)

    if fix:
        result = _apply_fixes(check_run, result)

    if not quiet:
        _report(result, output_format, limit)
    raise typer.Exit(_exit_code(result))


def _exit_code(result: RunResult) -> int:
    if result.failed_rules:
        return EXIT_INTERNAL_ERROR
    return EXIT_FOUND_ERRORS if result.has_errors else EXIT_OK


def _report_failures(result: RunResult) -> None:
    # В stderr: stdout в этих ветках занят diff-ом или молчит.
    for failed in result.failed_rules:
        err_console.print(f"Правило {failed.rule_id} упало и пропущено: {failed.error}")


@dataclass(frozen=True, slots=True)
class _Check:
    """Один прогон проверки. Ключ ``--fix`` повторяет его после каждой правки."""

    paths: list[Path]
    rules: tuple[RuleImpl, ...]
    profile: Profile
    baseline: Baseline | None
    ignored: frozenset[str]
    known_ids: frozenset[str]
    threshold: Severity

    def __call__(self, overlay: dict[Path, str] | None = None) -> RunResult:
        parsed = parse(self.paths, self.profile, overlay)
        return run(
            parsed.document,
            self.rules,
            extra_findings=parse_findings(parsed),
            threshold=self.threshold,
            suppressions=parsed.suppressions,
            baseline=self.baseline,
            ignored=self.ignored,
            known_ids=self.known_ids,
        )


def _diff(check_run: _Check, result: RunResult) -> str:
    """Показать всё, что сделал бы ``--fix``, ничего не записывая."""
    overlay: dict[Path, str] = {}
    for _ in range(FIX_PASSES):
        prepared = plan(result.findings, overlay)
        if not prepared.applied:
            break
        overlay.update({edit.path: edit.text for edit in prepared.edits})
        result = check_run(overlay)
    return diff(overlay)


def _apply_fixes(check_run: _Check, result: RunResult) -> RunResult:
    """Применять правки, пока они находятся, и перепроверять исходники.

    Проходов несколько: пересекающиеся правки в один проход не применяются,
    а исправленное место может открыть следующее нарушение.
    """
    before = {finding.rule_id for finding in result.findings}
    applied = 0
    incomplete = True
    reported: set[Path] = set()
    for _ in range(FIX_PASSES):
        prepared = plan(result.findings)
        for path in prepared.skipped:
            if path not in reported:
                reported.add(path)
                err_console.print(f"Не удалось прочитать как UTF-8, пропущен: {path}")
        if not prepared.applied:
            incomplete = False
            break
        written = write(prepared)
        for path, reason in written.failed:
            if path not in reported:
                reported.add(path)
                err_console.print(f"Не удалось записать, пропущен: {path} — {reason}")
        applied += written.applied
        if not written.applied:
            # Записать не удалось ничего: следующий проход повторил бы то же самое.
            break
        result = check_run()

    if applied:
        console.print(f"Исправлено находок: {applied}.")
    _report_fix_result(result, before=before, incomplete=incomplete)
    return result


def _report_fix_result(result: RunResult, before: set[str], incomplete: bool) -> None:
    """Сказать, чем кончились правки: молчаливый успех скрывал бы регресс.

    Правка может открыть нарушение, которого в отчёте не было, а пересекающиеся
    правки могут не разойтись за отведённые проходы. Сравнивается состав правил:
    номера строк и число находок правки двигают сами.
    """
    opened = sorted({finding.rule_id for finding in result.findings} - before)
    if opened:
        err_console.print(
            f"Правки открыли нарушения, которых не было: {', '.join(opened)}. "
            "Проверьте правки: nk check --diff"
        )
    remaining = sum(1 for finding in result.findings if finding.fix is not None)
    if incomplete and remaining:
        err_console.print(
            f"Правки применены не полностью: осталось с машинной правкой {remaining}. "
            "Повторите запуск."
        )


def _write_baseline(path: Path, result: RunResult) -> None:
    snapshot = Baseline.of(result.findings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.dumps(__version__), encoding="utf-8")
    console.print(f"Записано находок в снимок: {len(result.findings)} → {path}")


def _report(result: RunResult, output_format: OutputFormat, limit: int) -> None:
    # agent и json пишутся в stdout напрямую: Rich переносил бы длинные строки,
    # а оба формата копируются и разбираются как есть.
    command = " ".join(["nk", *sys.argv[1:]])
    if output_format is OutputFormat.JSON:
        sys.stdout.write(json_report.render(result))
    elif output_format is OutputFormat.AGENT:
        sys.stdout.write(agent.render(result, command=command, limit=limit))
    else:
        human.render(result, console, command=command)


def _split(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@rules_app.command("docs")
def rules_docs_command(
    output: Path = typer.Option(
        Path("docs/rules"), "--output", "-o", help="Каталог, куда записать страницы правил."
    ),
    fixtures: Path = typer.Option(
        examples.DEFAULT_FIXTURES_ROOT,
        "--fixtures",
        help="Каталог фикстур, из которых берутся примеры.",
    ),
) -> None:
    """Сгенерировать страницы документации по правилам."""
    registry = load_rules()
    written, removed = rules_docs.write_pages(registry, output, fixtures_root=fixtures)
    console.print(f"Записано страниц: {written} → {output}")
    if removed:
        console.print(f"Удалено устаревших: {removed}")
