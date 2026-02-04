"""Beyond Ralph CLI - Main entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="beyond-ralph",
    help="True Autonomous Coding - Multi-agent orchestration for Claude Code",
    no_args_is_help=True,
)
console = Console()


def run_async(coro):
    """Run async function from sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(coro)
    else:
        return asyncio.run(coro)


@app.command()
def start(
    spec: str = typer.Option(..., "--spec", "-s", help="Path to specification file"),
    safemode: bool = typer.Option(
        False, "--safemode", help="Require permissions for dangerous operations"
    ),
) -> None:
    """Start a new autonomous development project."""
    spec_path = Path(spec)

    if not spec_path.exists():
        console.print(f"[bold red]Error:[/bold red] Specification file not found: {spec}")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold green]Starting Beyond Ralph[/bold green]\n\n"
        f"Specification: {spec_path.absolute()}\n"
        f"Safe mode: {'[yellow]enabled[/yellow]' if safemode else '[green]disabled[/green]'}",
        title="Beyond Ralph",
        border_style="green",
    ))

    async def run_orchestrator():
        from beyond_ralph.core.orchestrator import Orchestrator

        orchestrator = Orchestrator(
            project_root=Path.cwd(),
            safemode=safemode,
        )

        await orchestrator.start(spec_path)

    try:
        run_async(run_orchestrator())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Use /beyond-ralph:resume to continue.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def resume(
    project_id: str | None = typer.Option(
        None, "--project", "-p", help="Project UUID to resume"
    ),
) -> None:
    """Resume a paused or interrupted project."""
    console.print(Panel(
        "[bold blue]Resuming Beyond Ralph project[/bold blue]",
        title="Beyond Ralph",
        border_style="blue",
    ))

    if project_id:
        console.print(f"Project: {project_id}")
    else:
        console.print("Resuming most recent project...")

    async def run_resume():
        from beyond_ralph.core.orchestrator import Orchestrator

        orchestrator = Orchestrator(project_root=Path.cwd())
        await orchestrator.resume(project_id)

    try:
        run_async(run_resume())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show status of current project and agents."""
    async def get_status():
        from beyond_ralph.core.orchestrator import Orchestrator

        orchestrator = Orchestrator(project_root=Path.cwd())
        return await orchestrator.status()

    try:
        status_info = run_async(get_status())

        table = Table(title="Beyond Ralph Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project ID", status_info.project_id)
        table.add_row("Phase", f"{status_info.phase.name} ({status_info.phase.value}/8)")
        table.add_row("State", status_info.state.value)
        table.add_row("Progress", f"{status_info.progress_percent:.1f}%")

        console.print(table)

        if status_info.current_task:
            console.print(f"\n[bold]Current Task:[/bold] {status_info.current_task}")

        if status_info.active_agents > 0:
            console.print(f"[bold]Active Agents:[/bold] {status_info.active_agents}")

    except FileNotFoundError:
        console.print("[yellow]No active project found.[/yellow]")
        console.print("Start a new project with: beyond-ralph start --spec <path>")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def pause() -> None:
    """Pause the current project."""
    async def run_pause():
        from beyond_ralph.core.orchestrator import Orchestrator

        orchestrator = Orchestrator(project_root=Path.cwd())
        await orchestrator.pause()

    try:
        run_async(run_pause())
        console.print("[green]Beyond Ralph paused.[/green]")
        console.print("Resume with: beyond-ralph resume")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def quota() -> None:
    """Check Claude usage quota status."""
    from beyond_ralph.utils.quota_checker import check_and_display_quota
    check_and_display_quota()


@app.command()
def info() -> None:
    """Show system information and capabilities."""
    from beyond_ralph.utils.system import get_extended_capabilities

    caps = get_extended_capabilities()

    table = Table(title="System Capabilities")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Platform", caps["platform"])
    table.add_row("Architecture", caps["architecture"])
    table.add_row("Package Manager", caps["package_manager"])
    table.add_row("Passwordless Sudo", "Yes" if caps["has_passwordless_sudo"] else "No")
    table.add_row("WSL2", "Yes" if caps["is_wsl2"] else "No")
    table.add_row("Has Display", "Yes" if caps["has_display"] else "No")

    console.print(table)

    if caps["available_tools"]:
        console.print(f"\n[bold]Available Tools:[/bold] {', '.join(caps['available_tools'][:20])}")
        if len(caps["available_tools"]) > 20:
            console.print(f"... and {len(caps['available_tools']) - 20} more")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
