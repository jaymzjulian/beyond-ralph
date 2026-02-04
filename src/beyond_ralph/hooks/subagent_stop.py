"""SubagentStop hook for handling subagent completion.

This hook is triggered when a subagent completes (successfully or with failure).
It captures the result and routes it back to the orchestrator.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def handle_subagent_stop(
    session_id: str | None = None,
    result: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Handle a subagent stopping.

    This is called when a subagent completes. It:
    1. Records the result/error
    2. Updates the session state
    3. Notifies the orchestrator

    Args:
        session_id: ID of the subagent session.
        result: Final result from the subagent.
        success: Whether the subagent completed successfully.
        error: Error message if failed.
    """
    try:
        state_file = Path.cwd() / ".beyond_ralph_subagent_results.json"

        # Load existing results
        results: dict = {}
        if state_file.exists():
            try:
                results = json.loads(state_file.read_text())
            except json.JSONDecodeError:
                results = {}

        # Add this result
        if session_id:
            results[session_id] = {
                "session_id": session_id,
                "success": success,
                "result": result,
                "error": error,
                "completed_at": datetime.now().isoformat(),
            }

            state_file.write_text(json.dumps(results, indent=2))

            # Log the completion
            status = "completed" if success else "FAILED"
            print(f"[BEYOND-RALPH] Subagent {session_id} {status}", file=sys.stderr)

    except Exception as e:
        print(f"[BEYOND-RALPH] Warning: Failed to record subagent result: {e}", file=sys.stderr)


def get_subagent_result(session_id: str) -> dict | None:
    """Get the result from a completed subagent.

    Args:
        session_id: ID of the subagent.

    Returns:
        Result dictionary or None if not found.
    """
    state_file = Path.cwd() / ".beyond_ralph_subagent_results.json"

    if not state_file.exists():
        return None

    try:
        results = json.loads(state_file.read_text())
        return results.get(session_id)
    except (json.JSONDecodeError, KeyError):
        return None


def clear_subagent_result(session_id: str) -> bool:
    """Clear a subagent result after it has been processed.

    Args:
        session_id: ID of the subagent.

    Returns:
        True if cleared successfully.
    """
    state_file = Path.cwd() / ".beyond_ralph_subagent_results.json"

    if not state_file.exists():
        return False

    try:
        results = json.loads(state_file.read_text())
        if session_id in results:
            del results[session_id]
            state_file.write_text(json.dumps(results, indent=2))
            return True
    except (json.JSONDecodeError, KeyError):
        pass

    return False


def get_all_pending_results() -> dict[str, dict]:
    """Get all pending subagent results.

    Returns:
        Dictionary of session_id -> result.
    """
    state_file = Path.cwd() / ".beyond_ralph_subagent_results.json"

    if not state_file.exists():
        return {}

    try:
        return json.loads(state_file.read_text())
    except json.JSONDecodeError:
        return {}


def main() -> None:
    """Entry point for hook execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Handle subagent completion")
    parser.add_argument("--session-id", help="Subagent session ID")
    parser.add_argument("--result", help="Final result")
    parser.add_argument("--success", type=bool, default=True, help="Whether successful")
    parser.add_argument("--error", help="Error message if failed")

    args = parser.parse_args()

    handle_subagent_stop(
        session_id=args.session_id,
        result=args.result,
        success=args.success,
        error=args.error,
    )


if __name__ == "__main__":
    main()
