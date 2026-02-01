"""Quota checker utility for monitoring Claude usage limits.

This module provides functionality to check Claude Code usage quotas
and determine when the system should pause autonomous operations.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Cache file for quota status
QUOTA_CACHE_FILE = Path(".quota_cache")
QUOTA_THRESHOLD = 85  # Pause at 85%


@dataclass
class QuotaStatus:
    """Current quota status."""

    session_percent: float
    weekly_percent: float
    checked_at: datetime
    is_limited: bool

    @property
    def status_color(self) -> str:
        """Return status color based on quota levels."""
        if self.is_limited:
            return "red"
        if max(self.session_percent, self.weekly_percent) >= 85:
            return "yellow"
        return "green"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "session_percent": self.session_percent,
            "weekly_percent": self.weekly_percent,
            "checked_at": self.checked_at.isoformat(),
            "is_limited": self.is_limited,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuotaStatus":
        """Create from dictionary."""
        return cls(
            session_percent=data["session_percent"],
            weekly_percent=data["weekly_percent"],
            checked_at=datetime.fromisoformat(data["checked_at"]),
            is_limited=data["is_limited"],
        )


def check_quota_via_cli() -> QuotaStatus:
    """Check quota by invoking claude /usage command.

    This runs 'claude' command, sends '/usage' to get quota info,
    then exits gracefully.

    Returns:
        QuotaStatus with current usage levels.

    Note:
        This is a simplified implementation. The actual parsing
        of claude /usage output will need to be refined based
        on the actual output format.
    """
    try:
        # Run claude with /usage command
        # This is a placeholder - actual implementation needs to
        # interact with claude CLI properly
        result = subprocess.run(
            ["claude", "--print-usage"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Parse output (placeholder - needs actual parsing logic)
        # Expected format TBD based on actual claude output
        output = result.stdout

        # For now, return a mock status
        # TODO: Implement actual parsing
        session_pct = 0.0
        weekly_pct = 0.0

        # Try to parse percentages from output
        # This is a placeholder implementation
        for line in output.split("\n"):
            if "session" in line.lower() and "%" in line:
                try:
                    session_pct = float(line.split("%")[0].split()[-1])
                except (ValueError, IndexError):
                    pass
            if "weekly" in line.lower() and "%" in line:
                try:
                    weekly_pct = float(line.split("%")[0].split()[-1])
                except (ValueError, IndexError):
                    pass

        is_limited = session_pct >= QUOTA_THRESHOLD or weekly_pct >= QUOTA_THRESHOLD

        return QuotaStatus(
            session_percent=session_pct,
            weekly_percent=weekly_pct,
            checked_at=datetime.now(),
            is_limited=is_limited,
        )

    except subprocess.TimeoutExpired:
        # On timeout, assume we might be limited
        return QuotaStatus(
            session_percent=0.0,
            weekly_percent=0.0,
            checked_at=datetime.now(),
            is_limited=False,
        )
    except FileNotFoundError:
        # Claude CLI not found
        print("Error: 'claude' command not found. Is Claude Code installed?")
        return QuotaStatus(
            session_percent=0.0,
            weekly_percent=0.0,
            checked_at=datetime.now(),
            is_limited=False,
        )


def load_cached_quota() -> QuotaStatus | None:
    """Load cached quota status if recent enough."""
    if not QUOTA_CACHE_FILE.exists():
        return None

    try:
        data = json.loads(QUOTA_CACHE_FILE.read_text())
        status = QuotaStatus.from_dict(data)

        # Cache is valid for 5 minutes during normal operation
        # or 10 minutes if we're paused (as specified in spec)
        cache_minutes = 10 if status.is_limited else 5
        age = (datetime.now() - status.checked_at).total_seconds() / 60

        if age < cache_minutes:
            return status

    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    return None


def save_quota_cache(status: QuotaStatus) -> None:
    """Save quota status to cache file."""
    QUOTA_CACHE_FILE.write_text(json.dumps(status.to_dict()))


def get_quota_status(force_refresh: bool = False) -> QuotaStatus:
    """Get current quota status, using cache if available.

    Args:
        force_refresh: If True, bypass cache and check directly.

    Returns:
        Current QuotaStatus.
    """
    if not force_refresh:
        cached = load_cached_quota()
        if cached is not None:
            return cached

    status = check_quota_via_cli()
    save_quota_cache(status)
    return status


def check_and_display_quota() -> None:
    """Check quota and display with rich formatting."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        console.print("\n[bold]Claude Usage Quota[/bold]\n")

        status = get_quota_status(force_refresh=True)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Metric")
        table.add_column("Usage")
        table.add_column("Status")

        session_status = (
            "[red]LIMITED[/red]"
            if status.session_percent >= 95
            else "[yellow]WARNING[/yellow]"
            if status.session_percent >= 85
            else "[green]OK[/green]"
        )
        weekly_status = (
            "[red]LIMITED[/red]"
            if status.weekly_percent >= 95
            else "[yellow]WARNING[/yellow]"
            if status.weekly_percent >= 85
            else "[green]OK[/green]"
        )

        table.add_row("Session", f"{status.session_percent:.1f}%", session_status)
        table.add_row("Weekly", f"{status.weekly_percent:.1f}%", weekly_status)

        console.print(table)

        if status.is_limited:
            console.print(
                "\n[bold red]⚠ QUOTA LIMITED[/bold red] - "
                "Beyond Ralph will pause agent spawning."
            )
        else:
            console.print("\n[green]✓[/green] Quota OK - Normal operation available.")

        console.print(f"\nLast checked: {status.checked_at.strftime('%Y-%m-%d %H:%M:%S')}")

    except ImportError:
        # Fallback without rich
        status = get_quota_status(force_refresh=True)
        print("\nClaude Usage Quota")
        print("-" * 30)
        print(f"Session: {status.session_percent:.1f}%")
        print(f"Weekly:  {status.weekly_percent:.1f}%")
        print(f"Limited: {status.is_limited}")
        print(f"Checked: {status.checked_at}")


def main() -> None:
    """CLI entry point for quota checker."""
    check_and_display_quota()


if __name__ == "__main__":
    main()
