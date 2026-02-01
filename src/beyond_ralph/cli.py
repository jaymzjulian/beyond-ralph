"""Beyond Ralph CLI - Main entry point."""

import typer
from rich.console import Console

app = typer.Typer(
    name="beyond-ralph",
    help="True Autonomous Coding - Multi-agent orchestration for Claude Code",
    no_args_is_help=True,
)
console = Console()


@app.command()
def start(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to specification file"),
    safemode: bool = typer.Option(
        False, "--safemode", help="Require permissions for dangerous operations"
    ),
) -> None:
    """Start a new autonomous development project."""
    console.print(f"[bold green]Starting Beyond Ralph[/bold green]")
    console.print(f"Specification: {spec}")
    console.print(f"Safe mode: {'enabled' if safemode else 'disabled'}")
    # TODO: Implement orchestrator startup
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def resume(
    project_id: str | None = typer.Option(
        None, "--project", "-p", help="Project UUID to resume"
    ),
) -> None:
    """Resume a paused or interrupted project."""
    console.print("[bold blue]Resuming Beyond Ralph project[/bold blue]")
    if project_id:
        console.print(f"Project: {project_id}")
    else:
        console.print("Resuming most recent project...")
    # TODO: Implement resume logic
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def status() -> None:
    """Show status of current project and agents."""
    console.print("[bold]Beyond Ralph Status[/bold]")
    # TODO: Implement status display
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def quota() -> None:
    """Check Claude usage quota status."""
    from beyond_ralph.utils.quota_checker import check_and_display_quota
    check_and_display_quota()


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
