#!/usr/bin/env python3
"""Beyond Ralph Stop Hook - Keeps orchestrator running until complete.

Modeled after ralph-wiggum plugin (anthropics/claude-code).
The key insight: re-feed the SAME PROMPT back via "reason" field.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def debug_log(msg: str) -> None:
    """Append to debug log file."""
    try:
        with Path(".beyond_ralph_hook_debug.log").open("a") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} - {msg}\n")
    except Exception:
        pass


def allow_exit() -> None:
    """Allow Claude to stop (exit cleanly with no JSON)."""
    sys.exit(0)


def block_exit(prompt: str, iteration: int, incomplete: int) -> None:
    """Block Claude from stopping and re-feed the prompt."""
    result = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": f"\U0001f504 Beyond Ralph iteration {iteration} | {incomplete} tasks remaining | Output AUTOMATION_COMPLETE when done"
    }
    debug_log(f"Returning block: iteration={iteration}, incomplete={incomplete}")
    debug_log(f"  JSON (first 300): {json.dumps(result)[:300]}...")
    # Only stdout output is the JSON
    print(json.dumps(result))
    sys.exit(0)


def main() -> None:
    """Main stop hook logic."""
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        hook_input = {}

    stop_hook_active = hook_input.get("stop_hook_active", False)
    transcript_path = hook_input.get("transcript_path", "")

    debug_log(f"Stop hook invoked (stop_hook_active={stop_hook_active})")

    # Check if Beyond Ralph state file exists
    state_file = Path(".beyond_ralph_state")
    if not state_file.exists():
        debug_log("No state file - allowing exit")
        allow_exit()

    try:
        state = json.loads(state_file.read_text())
    except Exception:
        debug_log("State file unreadable - allowing exit")
        allow_exit()

    br_state = state.get("state", "unknown")

    # Terminal states - allow exit
    terminal_states = ("complete", "done", "finished", "stopped", "cancelled", "error")
    if br_state in terminal_states:
        debug_log(f"Terminal state ({br_state}) - allowing exit")
        allow_exit()

    # Human wait states - allow exit
    human_wait_states = ("waiting_for_human", "awaiting_input", "blocked_on_user", "needs_human")
    if br_state in human_wait_states:
        debug_log(f"Human wait state ({br_state}) - allowing exit")
        allow_exit()

    # Track iterations
    iteration = state.get("hook_iteration", 0) + 1
    max_iterations = state.get("max_iterations", 10000)

    if max_iterations > 0 and iteration > max_iterations:
        debug_log(f"Max iterations ({max_iterations}) reached - allowing exit")
        state["state"] = "stopped"
        state["stop_reason"] = "max_iterations"
        state_file.write_text(json.dumps(state, indent=2))
        allow_exit()

    # Check for AUTOMATION_COMPLETE in transcript (like ralph-wiggum checks <promise>)
    if transcript_path and Path(transcript_path).exists():
        try:
            last_text = ""
            for line in reversed(Path(transcript_path).read_text().strip().split("\n")):
                try:
                    msg = json.loads(line)
                    if msg.get("role") == "assistant":
                        content = msg.get("message", {}).get("content", [])
                        for block in content:
                            if block.get("type") == "text":
                                last_text += block.get("text", "")
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

            if "AUTOMATION_COMPLETE" in last_text:
                debug_log("Found AUTOMATION_COMPLETE in transcript - allowing exit")
                state["state"] = "complete"
                state_file.write_text(json.dumps(state, indent=2))
                allow_exit()

            if "PAUSED_FOR_QUOTA" in last_text or "QUOTA_LIMIT_REACHED" in last_text:
                debug_log("Found quota pause signal - allowing exit")
                state["state"] = "paused"
                state_file.write_text(json.dumps(state, indent=2))
                allow_exit()
        except Exception as e:
            debug_log(f"Transcript read error: {e}")

    # Check quota
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from beyond_ralph.utils.quota_checker import get_quota_status
        status = get_quota_status()
        if not status.is_unknown and (status.session_percent >= 85 or status.weekly_percent >= 85):
            debug_log(f"Quota limited ({status.session_percent}%/{status.weekly_percent}%) - allowing exit")
            state["state"] = "paused"
            state["pause_reason"] = "quota"
            state_file.write_text(json.dumps(state, indent=2))
            allow_exit()
    except Exception:
        pass  # Quota check failure = continue anyway

    # Count incomplete tasks
    incomplete = 0
    records_dir = Path("records")
    if records_dir.exists():
        for tf in records_dir.glob("*/tasks.md"):
            try:
                incomplete += tf.read_text().count("[ ]")
            except Exception:
                continue

    if incomplete == 0:
        debug_log("All tasks complete - allowing exit")
        state["state"] = "complete"
        state_file.write_text(json.dumps(state, indent=2))
        allow_exit()

    # === NOT COMPLETE - BLOCK EXIT AND RE-FEED PROMPT ===
    # Key insight from ralph-wiggum: feed the SAME PROMPT back, not generic instructions.
    # The prompt is stored in the state file by /beyond-ralph or /beyond-ralph-resume.

    # Update iteration
    state["hook_iteration"] = iteration
    state["last_activity"] = datetime.now(timezone.utc).isoformat()
    state_file.write_text(json.dumps(state, indent=2))

    # Get the stored prompt to re-feed (like ralph-wiggum's PROMPT_TEXT)
    prompt = state.get("prompt", "")

    if not prompt:
        # Fallback: build a prompt from state if none was stored
        phase = state.get("phase", "unknown")
        spec_path = state.get("spec_path", "")
        prompt = f"""You are the Beyond Ralph Orchestrator. You have {incomplete} incomplete tasks.

Read records/*/tasks.md to find incomplete tasks ([ ] checkboxes).
Use the Task tool to spawn agents for implementation and testing.
Mark checkboxes as complete [x] when verified.
Continue until ALL tasks have 6/6 checkboxes.

Phase: {phase} | Spec: {spec_path}

Output AUTOMATION_COMPLETE only when all {incomplete} remaining tasks are done."""

    block_exit(prompt, iteration, incomplete)


if __name__ == "__main__":
    main()
