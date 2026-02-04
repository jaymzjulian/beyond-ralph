"""Stop hook handler - Saves state when Claude Code session ends.

This hook is triggered when the Claude Code session is about to stop.
It ensures that Beyond Ralph's state is persisted so it can be resumed later.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def handle_stop() -> None:
    """Handle session stop by saving current state.

    This function is called by Claude Code's Stop hook.
    It saves the current orchestrator state to disk.
    """
    try:
        # Find the state file
        state_file = Path.cwd() / ".beyond_ralph_state"

        if state_file.exists():
            # Update the state with stop time
            state = json.loads(state_file.read_text())
            state["last_stopped"] = datetime.now(UTC).isoformat()
            state["status"] = "paused"

            state_file.write_text(json.dumps(state, indent=2))

            print(f"Beyond Ralph state saved to {state_file}")
            print("Resume with: /beyond-ralph:resume")

    except Exception as e:
        print(f"Warning: Could not save Beyond Ralph state: {e}", file=sys.stderr)


def main() -> None:
    """Entry point when run as a module."""
    handle_stop()


if __name__ == "__main__":
    main()
