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


def block_exit(prompt: str, iteration: int, incomplete: int, *, force_msg: str = "") -> None:
    """Block Claude from stopping and re-feed the prompt."""
    if force_msg:
        sys_msg = f"\U0001f504 Beyond Ralph iteration {iteration} | {force_msg}"
    elif incomplete > 0:
        sys_msg = f"\U0001f504 Beyond Ralph iteration {iteration} | {incomplete} tasks remaining | Output AUTOMATION_COMPLETE when done"
    else:
        # No checkbox-incomplete tasks but still blocking = prompt describes remaining work
        sys_msg = f"\U0001f504 Beyond Ralph iteration {iteration} | WORK REMAINS - read the prompt below and DO THE WORK NOW"
    result = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": sys_msg,
    }
    debug_log(f"Returning block: iteration={iteration}, incomplete={incomplete}")
    debug_log(f"  JSON (first 300): {json.dumps(result)[:300]}...")
    # Only stdout output is the JSON
    print(json.dumps(result))
    sys.exit(0)


def _check_quota_api() -> tuple[float | None, float]:
    """Check quota via Anthropic OAuth usage API (self-contained, no imports).

    Returns:
        Tuple of (session_percent, weekly_percent). session_percent is None if check failed.
    """
    import urllib.request
    import urllib.error

    creds_file = Path.home() / ".claude" / ".credentials.json"
    if not creds_file.exists():
        debug_log("No credentials file - skipping quota check")
        return None, 0

    try:
        creds = json.loads(creds_file.read_text())
        token = creds.get("claudeAiOauth", {}).get("accessToken", "")
        if not token:
            return None, 0
    except Exception:
        return None, 0

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
    except Exception as e:
        debug_log(f"Quota API error: {e}")
        return None, 0

    five_hour = data.get("five_hour", {})
    seven_day = data.get("seven_day", {})
    session_pct = float(five_hour.get("utilization", 0) or 0)
    weekly_pct = float(seven_day.get("utilization", 0) or 0)

    debug_log(f"Quota API: session={session_pct}%, weekly={weekly_pct}%")
    return session_pct, weekly_pct


def _run_audit_gate() -> tuple[bool, str]:
    """Run static audit as a gate before accepting AUTOMATION_COMPLETE.

    Returns:
        Tuple of (passed: bool, summary: str)
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from beyond_ralph.core.audit import quick_audit_for_hook
        return quick_audit_for_hook(Path.cwd())
    except ImportError:
        debug_log("Could not import audit module - skipping audit gate")
        return True, "Audit module not available (skipped)"
    except Exception as e:
        debug_log(f"Audit gate error: {e}")
        return True, f"Audit gate error (skipped): {e}"


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

    # User-requested stop states - always respect these (never override)
    user_stop_states = ("stopped", "cancelled", "error")
    if br_state in user_stop_states:
        debug_log(f"User-requested stop ({br_state}) - allowing exit")
        allow_exit()

    # Auto-completion states - verify against actual task records AND stored prompt
    auto_complete_states = ("complete", "done", "finished")
    if br_state in auto_complete_states:
        # Don't trust checkboxes alone. Check two things:
        # 1. Are there unchecked task checkboxes? (obvious incomplete work)
        # 2. Is there a stored prompt describing remaining work? (agents lied about checkboxes)
        actual_incomplete = 0
        records_dir = Path("records")
        if records_dir.exists():
            for tf in records_dir.glob("*/tasks.md"):
                try:
                    actual_incomplete += tf.read_text().count("[ ]")
                except Exception:
                    continue

        stored_prompt = state.get("prompt", "")
        has_remaining_work = bool(stored_prompt) and "AUTOMATION_COMPLETE" not in stored_prompt

        if actual_incomplete > 0 or has_remaining_work:
            reason = []
            if actual_incomplete > 0:
                reason.append(f"{actual_incomplete} tasks still incomplete")
            if has_remaining_work:
                reason.append("stored prompt describes remaining work")
            debug_log(f"State says '{br_state}' but {' and '.join(reason)} - overriding to running")
            state["state"] = "running"
            br_state = "running"
            state_file.write_text(json.dumps(state, indent=2))
            # Fall through to normal processing below
        else:
            debug_log(f"Terminal state ({br_state}), no incomplete tasks, no stored prompt - allowing exit")
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

            # Check if Claude intentionally declared completion.
            # Must be a standalone declaration, NOT just mentioning the phrase
            # in instructions like "Output AUTOMATION_COMPLETE when done".
            # Look for it at the start of a line or as a standalone statement.
            is_real_completion = False
            for text_line in last_text.split("\n"):
                stripped = text_line.strip()
                # Must START with AUTOMATION_COMPLETE (not "Output AUTOMATION_COMPLETE")
                if stripped.startswith("AUTOMATION_COMPLETE"):
                    is_real_completion = True
                    break

            if is_real_completion:
                debug_log("Found AUTOMATION_COMPLETE declaration - running audit gate...")
                # AUDIT GATE: Run static analysis before accepting completion
                audit_passed, audit_summary = _run_audit_gate()

                # Don't trust "skipped" audits - only trust real passes
                if "skipped" in audit_summary.lower() or "not available" in audit_summary.lower():
                    debug_log("Audit gate skipped (module not available) - not trusting")
                    audit_passed = False
                    audit_summary = "Audit module not available - cannot verify completion"

                if not audit_passed:
                    debug_log(f"Audit gate BLOCKED completion: {audit_summary}")
                    # Don't allow exit - force continuation with audit findings
                    audit_prompt = state.get("prompt", "")
                    if audit_prompt:
                        audit_prompt += (
                            f"\n\n**AUDIT GATE FAILED** - Cannot accept AUTOMATION_COMPLETE.\n"
                            f"{audit_summary}\n"
                            f"Fix ALL findings before declaring complete."
                        )
                    else:
                        audit_prompt = (
                            f"AUDIT GATE FAILED: {audit_summary}\n"
                            f"Fix all stubs, TODOs, and fake implementations, "
                            f"then output AUTOMATION_COMPLETE."
                        )
                    state["hook_iteration"] = iteration
                    state["last_activity"] = datetime.now(timezone.utc).isoformat()
                    state_file.write_text(json.dumps(state, indent=2))
                    block_exit(audit_prompt, iteration, incomplete=1)
                else:
                    debug_log(f"Audit gate passed: {audit_summary}")
                    state["state"] = "complete"
                    state_file.write_text(json.dumps(state, indent=2))
                    allow_exit()

            if "PAUSED_FOR_QUOTA" in last_text or "QUOTA_LIMIT_REACHED" in last_text:
                debug_log("Found quota pause signal - allowing exit")
                state["state"] = "paused"
                state_file.write_text(json.dumps(state, indent=2))
                allow_exit()

            # === DEFERRAL DETECTION ===
            # If Claude is listing "remaining work for future sessions" instead of
            # doing the work, extract the deferred items and force it to act NOW.
            deferral_phrases = [
                "future session",
                "remaining work",
                "future work",
                "next session",
                "later session",
                "out of scope",
                "deferred",
                "follow-up",
                "follow up session",
                "not addressed",
                "beyond current scope",
            ]
            last_lower = last_text.lower()
            found_deferral = any(phrase in last_lower for phrase in deferral_phrases)

            if found_deferral:
                debug_log("DEFERRAL DETECTED in Claude's response - extracting deferred work")
                # Extract the deferred items from Claude's response
                # Look for bullet points, numbered lists, or lines after deferral phrases
                deferred_items = []
                in_deferral_section = False
                for text_line in last_text.split("\n"):
                    line_lower = text_line.strip().lower()
                    # Detect start of a deferral list
                    if any(phrase in line_lower for phrase in deferral_phrases):
                        in_deferral_section = True
                        continue
                    # Collect bullet/numbered items in the deferral section
                    stripped = text_line.strip()
                    if in_deferral_section and stripped and (
                        stripped.startswith("-")
                        or stripped.startswith("*")
                        or stripped.startswith("•")
                        or (len(stripped) > 1 and stripped[0].isdigit() and stripped[1] in ".)")
                    ):
                        deferred_items.append(stripped.lstrip("-*•0123456789.) "))
                    # End section on blank line
                    elif in_deferral_section and not stripped:
                        in_deferral_section = False

                if deferred_items:
                    items_text = "\n".join(f"  - {item}" for item in deferred_items)
                    deferral_prompt = (
                        "**DEFERRAL REJECTED** - You listed work as 'remaining for future sessions'. "
                        "There are NO future sessions. The Zero Deferral Policy is MANDATORY.\n\n"
                        "You MUST complete ALL of the following work NOW:\n"
                        f"{items_text}\n\n"
                        "For each item:\n"
                        "1. Create a FIX task in the appropriate records/[module]/tasks.md\n"
                        "2. Spawn an implementation agent to do the work\n"
                        "3. Verify the work is complete\n\n"
                        "Do NOT output AUTOMATION_COMPLETE until ALL items above are resolved.\n"
                        "Do NOT defer anything. Do NOT say 'future session'. DO THE WORK NOW."
                    )
                else:
                    deferral_prompt = (
                        "**DEFERRAL REJECTED** - You mentioned 'future sessions' or 'remaining work' "
                        "that you're not completing. There are NO future sessions.\n\n"
                        "The Zero Deferral Policy is MANDATORY: if work remains, DO IT NOW.\n"
                        "Re-read records/*/tasks.md and the spec. Find incomplete work. Do it.\n\n"
                        "Do NOT output AUTOMATION_COMPLETE until ALL work is truly done.\n"
                        "Do NOT defer anything. DO THE WORK NOW."
                    )

                # Override the stored prompt with the forceful deferral prompt
                state["prompt"] = deferral_prompt
                state["hook_iteration"] = iteration
                state["last_activity"] = datetime.now(timezone.utc).isoformat()
                state_file.write_text(json.dumps(state, indent=2))
                block_exit(
                    deferral_prompt,
                    iteration,
                    incomplete=len(deferred_items) or 1,
                    force_msg=f"DEFERRAL REJECTED - {len(deferred_items) or 'unknown'} items must be completed NOW",
                )

        except Exception as e:
            debug_log(f"Transcript read error: {e}")

    # Count incomplete tasks (needed before quota check for block_exit)
    incomplete = 0
    records_dir = Path("records")
    if records_dir.exists():
        for tf in records_dir.glob("*/tasks.md"):
            try:
                incomplete += tf.read_text().count("[ ]")
            except Exception:
                continue

    # Check quota via API - if limited, block exit and tell Claude to wait for reset
    try:
        session_pct, weekly_pct = _check_quota_api()
        if session_pct is not None and (session_pct >= 85 or weekly_pct >= 85):
            debug_log(f"Quota limited ({session_pct}%/{weekly_pct}%) - blocking to wait")
            state["hook_iteration"] = iteration
            state["state"] = "waiting_for_quota"
            state["last_activity"] = datetime.now(timezone.utc).isoformat()
            state_file.write_text(json.dumps(state, indent=2))
            # Block exit with a prompt that tells Claude to wait and recheck
            quota_prompt = (
                f"QUOTA LIMITED: session={session_pct}%, weekly={weekly_pct}%.\n"
                f"You MUST wait for quota to reset before continuing.\n\n"
                f"Run this Python snippet to poll until quota is available:\n"
                f"```python\n"
                f"import time, json, urllib.request\n"
                f"creds = json.loads(open('{Path.home()}/.claude/.credentials.json').read())\n"
                f"token = creds['claudeAiOauth']['accessToken']\n"
                f"while True:\n"
                f"    time.sleep(600)  # Check every 10 minutes\n"
                f"    req = urllib.request.Request('https://api.anthropic.com/api/oauth/usage',\n"
                f"        headers={{'Authorization': f'Bearer {{token}}', 'anthropic-beta': 'oauth-2025-04-20'}})\n"
                f"    data = json.loads(urllib.request.urlopen(req, timeout=10).read())\n"
                f"    s = data.get('five_hour', {{}}).get('utilization', 0) or 0\n"
                f"    w = data.get('seven_day', {{}}).get('utilization', 0) or 0\n"
                f"    print(f'Quota check: session={{s}}%, weekly={{w}}%')\n"
                f"    if s < 85 and w < 85:\n"
                f"        print('Quota available! Resuming...')\n"
                f"        break\n"
                f"```\n\n"
                f"After quota resets, continue with the original task from the state file prompt.\n"
                f"Do NOT output AUTOMATION_COMPLETE. Do NOT pause. Resume work."
            )
            block_exit(quota_prompt, iteration, incomplete)
    except Exception as e:
        debug_log(f"Quota check error: {e} - continuing without quota gate")

    # Check incomplete tasks - but DO NOT trust checkboxes as sole source of truth.
    # Agents lie about their own work. If all boxes are checked but we have a stored
    # prompt describing remaining work, the prompt wins.
    prompt = state.get("prompt", "")
    if incomplete == 0 and not prompt:
        # No incomplete tasks AND no stored prompt = likely truly done.
        # But only AUTOMATION_COMPLETE (which goes through audit gate) should
        # set state to "complete". Here we just allow exit without forcing "complete"
        # so that /beyond-ralph-resume can still re-validate.
        debug_log("All checkboxes checked, no stored prompt - allowing exit (state unchanged)")
        allow_exit()

    # === NOT COMPLETE - BLOCK EXIT AND RE-FEED PROMPT ===
    # Key insight from ralph-wiggum: feed the SAME PROMPT back, not generic instructions.
    # The prompt is stored in the state file by /beyond-ralph or /beyond-ralph-resume.

    # Update iteration
    state["hook_iteration"] = iteration
    state["last_activity"] = datetime.now(timezone.utc).isoformat()
    state_file.write_text(json.dumps(state, indent=2))

    # prompt was already read from state above

    # SAFETY: If stored prompt is a stale DECLARATION of completion, discard it.
    # But DON'T discard prompts that merely INSTRUCT Claude to "Output AUTOMATION_COMPLETE
    # when done" - those are valid orchestrator prompts.
    # A stale prompt looks like "AUTOMATION_COMPLETE. All planned work is done."
    # A valid prompt looks like "Output AUTOMATION_COMPLETE only when all N tasks are done."
    stale_markers = ["All planned work is done", "AUTOMATION_COMPLETE."]
    if any(marker in prompt for marker in stale_markers):
        debug_log("Stored prompt is stale (contains completion declaration) - using fallback")
        prompt = ""

    if not prompt:
        # Fallback: build a prompt from state if none was stored
        phase = state.get("phase", "unknown")
        # Don't use "complete" as phase in the prompt - it confuses Claude
        if phase in ("complete", "done", "finished"):
            phase = "IMPLEMENTATION"
        spec_path = state.get("spec_path", state.get("spec_file", "SPEC.md"))
        prompt = f"""You are the Beyond Ralph Orchestrator. You have {incomplete} incomplete tasks.

Read records/*/tasks.md to find incomplete tasks ([ ] checkboxes).
Use the Task tool to spawn agents for implementation and testing.
Mark checkboxes as complete [x] when verified.
Continue until ALL tasks have 7/7 checkboxes.

Phase: {phase} | Spec: {spec_path}

Output AUTOMATION_COMPLETE only when all {incomplete} remaining tasks are done."""
        # Save the corrected prompt so future iterations use it
        state["prompt"] = prompt
        state["phase"] = phase
        state_file.write_text(json.dumps(state, indent=2))

    block_exit(prompt, iteration, incomplete)


if __name__ == "__main__":
    main()
