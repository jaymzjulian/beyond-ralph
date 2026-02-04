"""Claude Code hooks for Beyond Ralph.

This module provides hooks that integrate with Claude Code's hook system:
- stop_handler: Called when Claude Code session ends, saves state
- quota_check: Called before spawning agents, blocks if quota >= 85%
- subagent_stop: Called when a subagent completes, captures results
"""

from typing import Any


def register_hooks() -> dict[str, Any]:
    """Register Beyond Ralph hooks with Claude Code.

    This function is called by Claude Code's plugin system via the
    entry point defined in pyproject.toml.

    Returns:
        Dictionary of hook definitions.
    """
    return {
        "stop": {
            "name": "beyond-ralph-stop",
            "description": "Save Beyond Ralph state when session ends",
            "handler": "beyond_ralph.hooks.stop_handler:handle_stop",
        },
        "pre_spawn": {
            "name": "beyond-ralph-quota-check",
            "description": "Check quota before spawning child agents",
            "handler": "beyond_ralph.hooks.quota_check:check_quota_before_spawn",
        },
        "subagent_stop": {
            "name": "beyond-ralph-subagent-stop",
            "description": "Capture subagent results when they complete",
            "handler": "beyond_ralph.hooks.subagent_stop:handle_subagent_stop",
        },
    }
