"""Quota check hook - Checks quota before spawning agents.

This hook is triggered before the Task tool is used.
It checks if we're approaching quota limits and blocks agent spawns if needed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def check_quota_before_spawn() -> int:
    """Check quota before spawning a new agent.

    This function is called by Claude Code's PreToolUse hook for Task tool.

    Returns:
        0 if spawn is allowed, 1 if blocked due to quota
    """
    try:
        from beyond_ralph.core.quota_manager import QuotaManager

        manager = QuotaManager()
        status = manager.check()

        if status.is_limited:
            print(
                f"Beyond Ralph: Quota limit reached "
                f"(session: {status.session_percent:.1f}%, "
                f"weekly: {status.weekly_percent:.1f}%)",
                file=sys.stderr,
            )
            print("Pausing agent spawns until quota resets.", file=sys.stderr)

            # Update state file to indicate quota pause
            state_file = Path.cwd() / ".beyond_ralph_state"
            if state_file.exists():
                state = json.loads(state_file.read_text())
                state["status"] = "quota_paused"
                state["quota_info"] = status.to_dict()
                state_file.write_text(json.dumps(state, indent=2))

            return 1  # Block the spawn

        return 0  # Allow the spawn

    except ImportError:
        # QuotaManager not available, allow spawn
        return 0
    except Exception as e:
        print(f"Warning: Quota check failed: {e}", file=sys.stderr)
        return 0  # Allow spawn on error


def main() -> None:
    """Entry point when run as a module."""
    sys.exit(check_quota_before_spawn())


if __name__ == "__main__":
    main()
