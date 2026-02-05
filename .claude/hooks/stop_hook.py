#!/usr/bin/env python3
"""Beyond Ralph Stop Hook - Keeps orchestrator running until complete.

This hook:
1. Checks if Beyond Ralph is active and incomplete
2. Checks quota status (pauses at 85%+)
3. Blocks exit and feeds continuation prompt if work remains
4. Allows exit when complete or quota exceeded
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for quota_checker import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def read_hook_input() -> dict:
    """Read hook input from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception):
        return {}


def read_state() -> dict | None:
    """Read Beyond Ralph state file."""
    state_file = Path(".beyond_ralph_state")
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, Exception):
        return None


def write_state(state: dict) -> None:
    """Write Beyond Ralph state file."""
    state_file = Path(".beyond_ralph_state")
    state_file.write_text(json.dumps(state, indent=2))


def check_quota() -> tuple[bool, str]:
    """Check if quota is at or above limit.

    Returns:
        (is_limited, message) - True if at 85%+ quota
    """
    try:
        # Try to import the quota checker
        from beyond_ralph.utils.quota_checker import get_quota_status

        status = get_quota_status()

        if status.is_unknown:
            # Unknown = fail-safe, treat as limited
            return True, f"Quota unknown: {status.error_message}"
        if status.is_limited:
            return True, f"Quota at {status.session_percent:.0f}% session / {status.weekly_percent:.0f}% weekly"
        if status.session_percent >= 85 or status.weekly_percent >= 85:
            return True, f"Quota at {status.session_percent:.0f}% session / {status.weekly_percent:.0f}% weekly"
        return False, f"Quota OK: {status.session_percent:.0f}% session"
    except ImportError as e:
        # If quota checker not available, continue anyway (soft fail)
        return False, f"Quota checker not available: {e}"
    except Exception as e:
        return False, f"Quota check error: {e}"


def count_incomplete_tasks() -> int:
    """Count incomplete task checkboxes in records."""
    records_dir = Path("records")
    if not records_dir.exists():
        return 0

    incomplete = 0
    for tasks_file in records_dir.glob("*/tasks.md"):
        try:
            content = tasks_file.read_text()
            incomplete += content.count("[ ]")
        except Exception:
            continue
    return incomplete


def check_completion_in_transcript(transcript_path: str) -> str | None:
    """Check last assistant message for completion/pause signals.

    Returns:
        "complete" | "paused" | None
    """
    if not transcript_path or not Path(transcript_path).exists():
        return None

    try:
        # Read JSONL transcript
        lines = Path(transcript_path).read_text().strip().split("\n")

        # Find last assistant message
        last_assistant = None
        for line in reversed(lines):
            try:
                msg = json.loads(line)
                if msg.get("role") == "assistant":
                    last_assistant = msg
                    break
            except json.JSONDecodeError:
                continue

        if not last_assistant:
            return None

        # Extract text content
        content = last_assistant.get("message", {}).get("content", [])
        text = ""
        for block in content:
            if block.get("type") == "text":
                text += block.get("text", "")

        # Check for signals
        if "AUTOMATION_COMPLETE" in text:
            return "complete"
        if "PAUSED_FOR_QUOTA" in text or "QUOTA_LIMIT_REACHED" in text:
            return "paused"

        return None
    except Exception:
        return None


def build_continuation_prompt(state: dict, incomplete_tasks: int, quota_msg: str) -> str:
    """Build the prompt to continue working."""
    phase = state.get("phase", "unknown")
    spec_path = state.get("spec_path", "")

    return f"""You are the Beyond Ralph Orchestrator. CONTINUE WORKING.

Current state:
- Phase: {phase}
- Spec: {spec_path}
- Incomplete tasks: {incomplete_tasks}
- {quota_msg}

DO NOT STOP. Continue executing the current phase.
Check PROJECT_PLAN.md and records/*/tasks.md for what needs to be done.
Work through phases until ALL tasks have 6/6 checkboxes.

Use the Task tool to spawn agents for implementation and testing.
After EVERY action, check if you should continue to the next phase.

Output AUTOMATION_COMPLETE only when all tasks are truly complete (6/6 checkboxes)."""


def main():
    """Main stop hook logic."""
    # Read hook input
    hook_input = read_hook_input()
    transcript_path = hook_input.get("transcript_path", "")

    # Check if Beyond Ralph is active
    state = read_state()
    if not state:
        # No active project - allow exit
        sys.exit(0)

    br_state = state.get("state", "unknown")

    # Track iterations for safety (prevent truly infinite loops)
    # Default to 10000 - Beyond Ralph can run for days with many iterations
    iteration = state.get("hook_iteration", 0) + 1
    max_iterations = state.get("max_iterations", 10000)  # Very high for autonomous operation

    if iteration > max_iterations:
        print(f"🛑 Beyond Ralph: Max iterations ({max_iterations}) reached. Stopping.", file=sys.stderr)
        state["state"] = "stopped"
        state["stop_reason"] = "max_iterations"
        write_state(state)
        sys.exit(0)

    # Update iteration counter
    state["hook_iteration"] = iteration

    # Only allow exit if project is truly complete OR waiting for human input
    # Terminal states = work is done or blocked on external action
    # Any other state (running, in_progress, mvp_complete, etc.) should continue
    # if there are incomplete tasks
    terminal_states = ("complete", "done", "finished", "stopped", "cancelled", "error")
    # States that explicitly require human action - NOT "paused" which may be quota-related
    human_wait_states = ("waiting_for_human", "awaiting_input", "blocked_on_user", "needs_human")

    if br_state in terminal_states:
        print(f"✅ Beyond Ralph: Project in terminal state ({br_state})", file=sys.stderr)
        sys.exit(0)

    if br_state in human_wait_states:
        print(f"⏸️  Beyond Ralph: Waiting for human ({br_state})", file=sys.stderr)
        sys.exit(0)

    # Check for completion signals in transcript
    signal = check_completion_in_transcript(transcript_path)
    if signal == "complete":
        print("✅ Beyond Ralph: Project complete!", file=sys.stderr)
        state["state"] = "complete"
        write_state(state)
        sys.exit(0)
    elif signal == "paused":
        print("⏸️  Beyond Ralph: Paused by request", file=sys.stderr)
        state["state"] = "paused"
        write_state(state)
        sys.exit(0)

    # Check quota
    is_limited, quota_msg = check_quota()
    if is_limited:
        print(f"⏸️  Beyond Ralph: Paused for quota - {quota_msg}", file=sys.stderr)
        state["state"] = "paused"
        state["pause_reason"] = quota_msg
        write_state(state)
        sys.exit(0)

    # Count incomplete tasks
    incomplete_tasks = count_incomplete_tasks()

    if incomplete_tasks == 0:
        # All tasks complete!
        print("✅ Beyond Ralph: All tasks complete!", file=sys.stderr)
        state["state"] = "complete"
        write_state(state)
        sys.exit(0)

    # Not complete - continue working
    # Update state
    state["last_activity"] = datetime.now(timezone.utc).isoformat()
    write_state(state)

    # Build continuation prompt
    prompt = build_continuation_prompt(state, incomplete_tasks, quota_msg)

    # Output JSON to block exit and continue
    result = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": f"🔄 Beyond Ralph continuing... Phase: {state.get('phase', '?')} | {incomplete_tasks} tasks remaining | {quota_msg}"
    }

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
