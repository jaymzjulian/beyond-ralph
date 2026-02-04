"""Quota Manager for Beyond Ralph.

Monitors Claude usage quotas and pauses operations at 85% threshold.
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Quota threshold - PAUSE at this level
QUOTA_THRESHOLD = 85

# Cache settings
NORMAL_CACHE_MINUTES = 5
PAUSED_CACHE_MINUTES = 10

# Cache file location
QUOTA_CACHE_FILE = Path(".beyond_ralph_quota")


@dataclass
class QuotaStatus:
    """Current quota status."""

    session_percent: float
    weekly_percent: float
    checked_at: datetime
    is_limited: bool

    @property
    def status_level(self) -> str:
        """Get status level: green, yellow, or red."""
        max_pct = max(self.session_percent, self.weekly_percent)
        if max_pct >= 95:
            return "red"
        if max_pct >= 85:
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


class QuotaManager:
    """Manages quota checking and pausing behavior."""

    def __init__(
        self,
        threshold: int = QUOTA_THRESHOLD,
        cache_file: Path | None = None,
    ):
        """Initialize quota manager.

        Args:
            threshold: Percentage at which to pause (default 85).
            cache_file: Path to cache file.
        """
        self.threshold = threshold
        self.cache_file = cache_file or QUOTA_CACHE_FILE
        self._last_status: QuotaStatus | None = None
        self._paused = False

    async def _check_via_cli(self) -> QuotaStatus:
        """Check quota by invoking claude command.

        Runs in a temp directory to avoid polluting current session history.

        Returns:
            QuotaStatus with current levels.
        """
        import tempfile

        session_pct = 0.0
        weekly_pct = 0.0

        try:
            # Create temp dir to run in (avoids polluting session history)
            temp_dir = tempfile.mkdtemp(prefix="br_quota_")

            # Try to run claude with usage check
            # The exact command may vary based on Claude Code version
            result = subprocess.run(
                ["claude", "--print-usage"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_dir,  # Run in temp dir
            )

            # Clean up temp dir
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

            output = result.stdout

            # Parse percentages from output
            # This parsing logic needs to be refined based on actual output format
            for line in output.lower().split("\n"):
                if "session" in line and "%" in line:
                    try:
                        # Find number before %
                        import re
                        match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                        if match:
                            session_pct = float(match.group(1))
                    except (ValueError, AttributeError):
                        pass

                if "weekly" in line and "%" in line:
                    try:
                        import re
                        match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
                        if match:
                            weekly_pct = float(match.group(1))
                    except (ValueError, AttributeError):
                        pass

        except subprocess.TimeoutExpired:
            # On timeout, keep last known values
            if self._last_status:
                session_pct = self._last_status.session_percent
                weekly_pct = self._last_status.weekly_percent
        except FileNotFoundError:
            # Claude CLI not available
            pass

        is_limited = session_pct >= self.threshold or weekly_pct >= self.threshold

        return QuotaStatus(
            session_percent=session_pct,
            weekly_percent=weekly_pct,
            checked_at=datetime.now(),
            is_limited=is_limited,
        )

    def _load_cache(self) -> QuotaStatus | None:
        """Load cached quota status if recent enough."""
        if not self.cache_file.exists():
            return None

        try:
            data = json.loads(self.cache_file.read_text())
            status = QuotaStatus.from_dict(data)

            # Determine cache validity duration
            cache_minutes = PAUSED_CACHE_MINUTES if status.is_limited else NORMAL_CACHE_MINUTES
            age_seconds = (datetime.now() - status.checked_at).total_seconds()

            if age_seconds < cache_minutes * 60:
                return status

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

        return None

    def _save_cache(self, status: QuotaStatus) -> None:
        """Save quota status to cache."""
        self.cache_file.write_text(json.dumps(status.to_dict()))

    async def check(self, force_refresh: bool = False) -> QuotaStatus:
        """Check current quota status.

        Args:
            force_refresh: If True, bypass cache.

        Returns:
            Current QuotaStatus.
        """
        if not force_refresh:
            cached = self._load_cache()
            if cached is not None:
                self._last_status = cached
                self._paused = cached.is_limited
                return cached

        status = await self._check_via_cli()
        self._last_status = status
        self._paused = status.is_limited
        self._save_cache(status)

        return status

    def is_limited(self) -> bool:
        """Check if currently quota-limited.

        Returns:
            True if limited.
        """
        return self._paused

    async def wait_for_reset(self) -> None:
        """Wait until quota resets (checks every 10 minutes)."""
        while True:
            status = await self.check(force_refresh=True)
            if not status.is_limited:
                self._paused = False
                return

            # Wait 10 minutes before checking again
            await asyncio.sleep(PAUSED_CACHE_MINUTES * 60)

    async def pre_spawn_check(self) -> bool:
        """Check quota before spawning an agent.

        Should be called before each agent spawn.

        Returns:
            True if spawn is allowed, False if should pause.
        """
        status = await self.check()
        return not status.is_limited

    def get_summary(self) -> dict[str, Any]:
        """Get quota summary for display.

        Returns:
            Dict with quota information.
        """
        if self._last_status is None:
            return {
                "session_percent": 0,
                "weekly_percent": 0,
                "status": "unknown",
                "is_limited": False,
            }

        return {
            "session_percent": self._last_status.session_percent,
            "weekly_percent": self._last_status.weekly_percent,
            "status": self._last_status.status_level,
            "is_limited": self._last_status.is_limited,
            "checked_at": self._last_status.checked_at.isoformat(),
        }


# Singleton instance
_quota_manager: QuotaManager | None = None


def get_quota_manager(threshold: int = QUOTA_THRESHOLD) -> QuotaManager:
    """Get the quota manager singleton.

    Args:
        threshold: Quota threshold percentage.

    Returns:
        The QuotaManager instance.
    """
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager(threshold=threshold)
    return _quota_manager


async def check_quota() -> bool:
    """Convenience function to check if spawning is allowed.

    Returns:
        True if spawn is allowed.
    """
    manager = get_quota_manager()
    return await manager.pre_spawn_check()
