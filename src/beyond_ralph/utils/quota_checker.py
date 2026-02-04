"""Quota checker utility for monitoring Claude usage limits.

This module provides functionality to check Claude Code usage quotas
and determine when the system should pause autonomous operations.

CRITICAL: This module NEVER fakes results. If quota cannot be determined,
operations MUST be blocked until quota can be verified. Unknown state = blocked.
"""

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Cache file for quota status
QUOTA_CACHE_FILE = Path(".quota_cache")
QUOTA_THRESHOLD = 85  # Pause at 85%


class QuotaCheckError(Exception):
    """Raised when quota cannot be determined."""
    pass


@dataclass
class QuotaStatus:
    """Current quota status.

    IMPORTANT: If quota check fails, we set is_unknown=True and treat
    as limited (fail-safe). We NEVER fake 0% usage.
    """

    session_percent: float
    weekly_percent: float
    checked_at: datetime
    is_limited: bool
    is_unknown: bool = False  # True if we couldn't determine quota
    error_message: str = ""

    @property
    def status_color(self) -> str:
        """Return status color based on quota levels."""
        if self.is_unknown:
            return "yellow"  # Unknown = warning, proceed with caution
        if self.is_limited:
            return "red"
        if max(self.session_percent, self.weekly_percent) >= 85:
            return "yellow"
        return "green"

    @property
    def can_proceed(self) -> bool:
        """Whether operations can proceed.

        CRITICAL: Unknown quota = cannot proceed (fail-safe).
        """
        if self.is_unknown:
            return False  # NEVER proceed when quota is unknown
        return not self.is_limited

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "session_percent": self.session_percent,
            "weekly_percent": self.weekly_percent,
            "checked_at": self.checked_at.isoformat(),
            "is_limited": self.is_limited,
            "is_unknown": self.is_unknown,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuotaStatus":
        """Create from dictionary."""
        return cls(
            session_percent=data["session_percent"],
            weekly_percent=data["weekly_percent"],
            checked_at=datetime.fromisoformat(data["checked_at"]),
            is_limited=data["is_limited"],
            is_unknown=data.get("is_unknown", False),
            error_message=data.get("error_message", ""),
        )

    @classmethod
    def unknown(cls, error: str) -> "QuotaStatus":
        """Create an unknown status (fail-safe - treated as limited)."""
        return cls(
            session_percent=-1,  # -1 indicates unknown
            weekly_percent=-1,
            checked_at=datetime.now(),
            is_limited=True,  # Fail-safe: treat unknown as limited
            is_unknown=True,
            error_message=error,
        )


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def check_quota_via_print_mode() -> QuotaStatus:
    """Check quota using claude --print mode.

    This is simpler and more reliable than interactive mode.
    We ask Claude directly about its quota status.

    Returns:
        QuotaStatus with current usage levels, or unknown status on failure.
    """
    import subprocess

    try:
        # Ask Claude about its quota using --print mode
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--dangerously-skip-permissions",
                "What is your current usage percentage? Reply with ONLY two numbers "
                "separated by a comma: session percentage, weekly percentage. "
                "For example: 45, 23. If you cannot determine this, reply: UNKNOWN",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout.strip()

        # Check for UNKNOWN response
        if "UNKNOWN" in output.upper():
            return QuotaStatus.unknown("Claude reported quota as unknown")

        # Try to parse the response
        # Look for patterns like "45, 23" or "45,23" or "45 23"
        numbers = re.findall(r"(\d+(?:\.\d+)?)", output)

        if len(numbers) >= 2:
            session_pct = float(numbers[0])
            weekly_pct = float(numbers[1])

            is_limited = (
                session_pct >= QUOTA_THRESHOLD or weekly_pct >= QUOTA_THRESHOLD
            )

            return QuotaStatus(
                session_percent=session_pct,
                weekly_percent=weekly_pct,
                checked_at=datetime.now(),
                is_limited=is_limited,
                is_unknown=False,
            )

        # Couldn't parse
        return QuotaStatus.unknown(f"Could not parse quota from response: {output[:100]}")

    except subprocess.TimeoutExpired:
        return QuotaStatus.unknown("Quota check timed out")
    except FileNotFoundError:
        return QuotaStatus.unknown("'claude' command not found")
    except Exception as e:
        return QuotaStatus.unknown(f"Error checking quota: {e}")


def _kill_process_tree(pid: int) -> None:
    """Kill a process and all its children."""
    import signal
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        parent.kill()
    except Exception:
        # Fallback to simple kill
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


def _single_quota_check_attempt() -> QuotaStatus:
    """Single attempt to check quota via CLI.

    Returns:
        QuotaStatus with results or unknown status on failure.
    """
    import pexpect

    child = None
    try:
        # Set terminal environment
        os.environ['TERM'] = 'xterm-256color'

        # ALWAYS use home directory - it's trusted
        home = os.path.expanduser("~")

        # Start claude interactively with generous timeout
        child = pexpect.spawn(
            'claude',
            encoding='utf-8',
            timeout=90,  # Generous timeout
            dimensions=(60, 180),  # Wide terminal for output
            cwd=home,
            env={**os.environ, 'TERM': 'xterm-256color'}
        )

        all_output = ""

        # Wait for initial prompt and drain
        time.sleep(4)
        for _ in range(6):
            try:
                chunk = child.read_nonblocking(size=50000, timeout=1)
                all_output += chunk
            except pexpect.TIMEOUT:
                break

        # Handle trust prompt if present
        if 'trust' in all_output.lower() or 'Yes, I trust' in all_output:
            child.send('1')  # Accept trust
            time.sleep(0.3)
            child.send('\r')
            time.sleep(5)  # Wait for main screen to load

            # Drain main screen output
            for _ in range(5):
                try:
                    chunk = child.read_nonblocking(size=50000, timeout=1)
                    all_output += chunk
                except pexpect.TIMEOUT:
                    break

        # Send /usage command
        child.send('/usage')
        time.sleep(0.5)
        child.send('\r')  # Enter

        # Wait for usage screen to fully load and render
        time.sleep(12)

        # Read all available output
        read_start = time.time()
        while time.time() - read_start < 15:
            try:
                chunk = child.read_nonblocking(size=50000, timeout=1)
                all_output += chunk
            except pexpect.TIMEOUT:
                break
            except pexpect.EOF:
                break

        # Clean the output
        cleaned = strip_ansi(all_output)
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '\n', cleaned)

        # Parse for quota percentages
        session_pct = None
        weekly_pct = None

        lines = cleaned.split('\n')

        # Strategy 1: Look for "X% used" patterns with context
        for i, line in enumerate(lines):
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*used', line.lower())
            if pct_match:
                pct_val = float(pct_match.group(1))
                prev_context = ' '.join(lines[max(0, i-5):i+1]).lower()

                if 'current session' in prev_context and session_pct is None:
                    session_pct = pct_val
                elif 'current week' in prev_context and 'all models' in prev_context:
                    if weekly_pct is None:
                        weekly_pct = pct_val
                elif 'week' in prev_context and 'sonnet' not in prev_context:
                    if weekly_pct is None:
                        weekly_pct = pct_val
                elif session_pct is None and 'session' in prev_context:
                    session_pct = pct_val

        # Strategy 2: Look for section headers and find % in following lines
        if session_pct is None or weekly_pct is None:
            for i, line in enumerate(lines):
                line_lower = line.lower()

                if session_pct is None and 'current session' in line_lower:
                    for j in range(i + 1, min(i + 6, len(lines))):
                        match = re.search(r'(\d+(?:\.\d+)?)\s*%', lines[j])
                        if match:
                            session_pct = float(match.group(1))
                            break

                if weekly_pct is None and 'current week' in line_lower:
                    if 'sonnet' not in line_lower:
                        for j in range(i + 1, min(i + 6, len(lines))):
                            match = re.search(r'(\d+(?:\.\d+)?)\s*%', lines[j])
                            if match:
                                weekly_pct = float(match.group(1))
                                break

        # Strategy 3: Just find any percentages and use first two
        if session_pct is None and weekly_pct is None:
            all_pcts = re.findall(r'(\d+(?:\.\d+)?)\s*%', cleaned)
            if len(all_pcts) >= 2:
                # Assume first is session, second is weekly
                session_pct = float(all_pcts[0])
                weekly_pct = float(all_pcts[1])
            elif len(all_pcts) == 1:
                session_pct = float(all_pcts[0])

        # CRITICAL: If we couldn't parse ANY quota, return unknown
        if session_pct is None and weekly_pct is None:
            sample = cleaned[:300].replace('\n', ' ')
            return QuotaStatus.unknown(
                f"Could not parse quota. Sample: {sample[:150]}..."
            )

        # Default missing values to 0 only if we got at least one
        session_pct = session_pct if session_pct is not None else 0.0
        weekly_pct = weekly_pct if weekly_pct is not None else 0.0

        # Check if limited
        is_limited = (
            session_pct >= QUOTA_THRESHOLD
            or weekly_pct >= QUOTA_THRESHOLD
            or "limited" in cleaned.lower()
            or "exceeded" in cleaned.lower()
        )

        return QuotaStatus(
            session_percent=session_pct,
            weekly_percent=weekly_pct,
            checked_at=datetime.now(),
            is_limited=is_limited,
            is_unknown=False,
        )

    finally:
        # ALWAYS clean up the child process
        if child is not None:
            try:
                child.send('\x1b')  # ESC to close any modal
                time.sleep(0.2)
                child.sendline('/quit')
                child.sendline('y')  # Confirm if asked
                try:
                    child.expect(pexpect.EOF, timeout=3)
                except pexpect.TIMEOUT:
                    pass
            except Exception:
                pass

            # Force kill if still running
            if child.isalive():
                _kill_process_tree(child.pid)


def check_quota_via_cli(max_retries: int = 3) -> QuotaStatus:
    """Check quota by invoking claude /usage command via pexpect.

    This runs 'claude' command interactively, sends '/usage' command,
    captures the usage screen output, then exits gracefully.

    ROBUST: Retries up to max_retries times on failure.
    CRITICAL: Returns unknown status (which blocks operations) if quota
    cannot be determined after all retries. We NEVER fake 0% usage.

    Args:
        max_retries: Maximum number of attempts (default 3).

    Returns:
        QuotaStatus with current usage levels, or unknown status on failure.
    """
    try:
        import pexpect
    except ImportError:
        return QuotaStatus.unknown("pexpect not installed - run: pip install pexpect")

    last_error = ""
    for attempt in range(max_retries):
        try:
            status = _single_quota_check_attempt()
            if not status.is_unknown:
                return status
            last_error = status.error_message
        except pexpect.exceptions.ExceptionPexpect as e:
            last_error = f"pexpect error: {e}"
        except FileNotFoundError:
            return QuotaStatus.unknown("'claude' command not found - is Claude Code installed?")
        except Exception as e:
            last_error = f"Unexpected error: {e}"

        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(2)

    return QuotaStatus.unknown(f"Failed after {max_retries} attempts. Last error: {last_error}")


def load_cached_quota() -> QuotaStatus | None:
    """Load cached quota status if recent enough."""
    if not QUOTA_CACHE_FILE.exists():
        return None

    try:
        data = json.loads(QUOTA_CACHE_FILE.read_text())
        status = QuotaStatus.from_dict(data)

        # Don't use cache if it was an unknown status
        if status.is_unknown:
            return None

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
        Current QuotaStatus. If unknown, operations should be blocked.

    Environment Variables:
        BEYOND_RALPH_QUOTA: Manually set quota as "session,weekly" (e.g., "27,19").
        BEYOND_RALPH_UNLIMITED: Set to "1" to assume unlimited quota.
        BEYOND_RALPH_ASSUME_OK: Set to "1" to assume quota is OK when check fails.
    """
    # Check for manual quota setting (most reliable - user provides from /usage screen)
    manual_quota = os.environ.get("BEYOND_RALPH_QUOTA", "").strip()
    if manual_quota:
        try:
            parts = manual_quota.split(",")
            if len(parts) >= 2:
                session_pct = float(parts[0].strip())
                weekly_pct = float(parts[1].strip())
                is_limited = session_pct >= QUOTA_THRESHOLD or weekly_pct >= QUOTA_THRESHOLD
                return QuotaStatus(
                    session_percent=session_pct,
                    weekly_percent=weekly_pct,
                    checked_at=datetime.now(),
                    is_limited=is_limited,
                    is_unknown=False,
                    error_message=f"Manual quota (BEYOND_RALPH_QUOTA={manual_quota})",
                )
        except ValueError:
            pass  # Fall through to other methods

    # Check for unlimited plan override
    if os.environ.get("BEYOND_RALPH_UNLIMITED", "").strip() == "1":
        return QuotaStatus(
            session_percent=0.0,
            weekly_percent=0.0,
            checked_at=datetime.now(),
            is_limited=False,
            is_unknown=False,
            error_message="Unlimited plan (BEYOND_RALPH_UNLIMITED=1)",
        )

    if not force_refresh:
        cached = load_cached_quota()
        if cached is not None:
            return cached

    # Try print mode first (simpler and more reliable)
    status = check_quota_via_print_mode()

    # If print mode failed, try interactive CLI mode as fallback
    if status.is_unknown:
        status = check_quota_via_cli()

    # Check for assume OK override (less safe, but useful for testing)
    if status.is_unknown and os.environ.get("BEYOND_RALPH_ASSUME_OK", "").strip() == "1":
        return QuotaStatus(
            session_percent=0.0,
            weekly_percent=0.0,
            checked_at=datetime.now(),
            is_limited=False,
            is_unknown=False,
            error_message="Assumed OK (BEYOND_RALPH_ASSUME_OK=1)",
        )

    # Only cache successful checks
    if not status.is_unknown:
        save_quota_cache(status)

    return status


def wait_for_quota_reset(check_interval_minutes: int = 10) -> QuotaStatus:
    """Wait for quota to reset, checking periodically.

    Args:
        check_interval_minutes: How often to check (default 10 per spec).

    Returns:
        QuotaStatus once quota is available.
    """
    print(f"Quota limited. Checking every {check_interval_minutes} minutes...")

    while True:
        status = get_quota_status(force_refresh=True)

        if status.can_proceed:
            print("Quota available! Resuming operations.")
            return status

        if status.is_unknown:
            print(f"Could not determine quota: {status.error_message}")
            print(f"Will retry in {check_interval_minutes} minutes...")
        else:
            print(f"Session: {status.session_percent:.1f}%, Weekly: {status.weekly_percent:.1f}%")
            print(f"Still limited. Waiting {check_interval_minutes} minutes...")

        time.sleep(check_interval_minutes * 60)


def check_and_display_quota() -> None:
    """Check quota and display with rich formatting."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        console.print("\n[bold]Claude Usage Quota[/bold]\n")

        status = get_quota_status(force_refresh=True)

        if status.is_unknown:
            console.print(Panel(
                f"[bold red]⚠ QUOTA CHECK FAILED[/bold red]\n\n"
                f"{status.error_message}\n\n"
                "[yellow]Operations are BLOCKED until quota can be verified.[/yellow]\n"
                "[dim]This is a safety measure - we never fake quota data.[/dim]",
                title="Unknown Status",
                border_style="red"
            ))
            return

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
            console.print(
                "[dim]Will auto-resume when quota resets. Checking every 10 minutes.[/dim]"
            )
        else:
            console.print("\n[green]✓[/green] Quota OK - Operations can proceed.")

        # Show if using override mode
        if status.error_message:
            console.print(f"\n[dim]Mode: {status.error_message}[/dim]")

        console.print(f"\nLast checked: {status.checked_at.strftime('%Y-%m-%d %H:%M:%S')}")

    except ImportError:
        # Fallback without rich
        status = get_quota_status(force_refresh=True)
        print("\nClaude Usage Quota")
        print("-" * 40)

        if status.is_unknown:
            print(f"ERROR: {status.error_message}")
            print("Operations BLOCKED - cannot verify quota")
            return

        print(f"Session: {status.session_percent:.1f}%")
        print(f"Weekly:  {status.weekly_percent:.1f}%")
        print(f"Limited: {status.is_limited}")
        print(f"Can Proceed: {status.can_proceed}")
        print(f"Checked: {status.checked_at}")


def main() -> None:
    """CLI entry point for quota checker."""
    check_and_display_quota()


if __name__ == "__main__":
    main()
