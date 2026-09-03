"""Команды CLI. Вся логика — в ядре; здесь только разбор аргументов и вывод."""

import typer
from rich.console import Console
from rich.table import Table

from nk import __version__
from nk.core.profile import ProfileError, load_profile
from nk.core.registry import load_rules, select_rules, validate_profile
from nk.core.rule import UnknownRuleError

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

EXIT_INTERNAL_ERROR = 2


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
