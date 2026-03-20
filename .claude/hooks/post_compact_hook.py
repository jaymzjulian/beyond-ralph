#!/usr/bin/env python3
"""Beyond Ralph Post-Compact Hook - Reestablish context after compaction.

When Claude Code auto-compacts (or user runs /compact), the orchestrator loses
detailed context about what it was working on. This hook detects an active
Beyond Ralph project and injects re-read instructions so the orchestrator
recovers gracefully.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def debug_log(msg: str) -> None:
    """Append to debug log file."""
    try:
        from datetime import UTC, datetime
        with Path(".beyond_ralph_hook_debug.log").open("a") as f:
            f.write(f"{datetime.now(UTC).isoformat()} - [COMPACT] {msg}\n")
    except Exception:
        pass


def main() -> None:
    """Post-compaction recovery: inject re-read instructions if project is active."""
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        # No input or bad JSON - nothing to do
        sys.exit(0)

    cwd = Path(hook_input.get("cwd", "."))
    trigger = hook_input.get("trigger", "unknown")
    debug_log(f"PostCompact fired: trigger={trigger}, cwd={cwd}")

    # Check if a Beyond Ralph project is active
    state_file = cwd / ".beyond_ralph_state"
    if not state_file.exists():
        debug_log("No .beyond_ralph_state - not a Beyond Ralph project, allowing")
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text())
    except Exception as e:
        debug_log(f"Failed to read state file: {e}")
        sys.exit(0)

    project_state = state.get("state", "")
    if project_state in ("complete", "done", "finished"):
        debug_log(f"Project state is '{project_state}' - no recovery needed")
        sys.exit(0)

    # Project is active - build recovery instructions
    phase = state.get("phase", "unknown")
    spec_path = state.get("spec_path", "SPEC.md")
    progress = state.get("progress_percent", "?")

    # Find which records directories exist
    records_dir = cwd / "records"
    modules = []
    if records_dir.exists():
        modules = sorted(d.name for d in records_dir.iterdir() if d.is_dir())

    knowledge_dir = cwd / "beyondralph_knowledge"
    knowledge_files = []
    if knowledge_dir.exists():
        knowledge_files = sorted(f.name for f in knowledge_dir.glob("*.md"))

    # Build the re-read instruction
    files_to_read = [".beyond_ralph_state"]
    if (cwd / spec_path).exists():
        files_to_read.append(spec_path)
    if (cwd / "PROJECT_PLAN.md").exists():
        files_to_read.append("PROJECT_PLAN.md")
    for mod in modules:
        tasks_file = f"records/{mod}/tasks.md"
        if (cwd / tasks_file).exists():
            files_to_read.append(tasks_file)
    for kf in knowledge_files[-5:]:  # Last 5 knowledge entries
        files_to_read.append(f"beyondralph_knowledge/{kf}")

    file_list = "\n".join(f"  - {f}" for f in files_to_read)

    recovery_msg = (
        f"COMPACTION RECOVERY (Beyond Ralph)\n"
        f"Context was compacted. You are the Beyond Ralph orchestrator.\n"
        f"Phase: {phase} | Progress: {progress}% | State: {project_state}\n"
        f"Modules: {', '.join(modules) if modules else 'none yet'}\n\n"
        f"MANDATORY: Re-read these files NOW to recover context:\n"
        f"{file_list}\n\n"
        f"After reading, find incomplete tasks (unchecked boxes in records/*/tasks.md) "
        f"and continue from where you left off. Do NOT restart from Phase 1.\n"
        f"Do NOT ask the user what to do - continue autonomously."
    )

    debug_log(f"Injecting recovery message for phase={phase}, {len(files_to_read)} files")

    # Output the system message for Claude to see after compaction
    result = {
        "systemMessage": recovery_msg
    }
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
