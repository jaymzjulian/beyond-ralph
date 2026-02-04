#!/bin/bash

# Beyond Ralph Stop Hook
# Prevents session exit when Beyond Ralph is running and incomplete
# Similar to ralph-loop but with Beyond Ralph specific logic

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Check if Beyond Ralph is active
BR_STATE_FILE=".beyond_ralph_state"

if [[ ! -f "$BR_STATE_FILE" ]]; then
  # No active project - allow exit
  exit 0
fi

# Parse JSON state file
STATE=$(cat "$BR_STATE_FILE")
BR_STATE=$(echo "$STATE" | jq -r '.state // "unknown"')
BR_PHASE=$(echo "$STATE" | jq -r '.phase // "unknown"')
SPEC_PATH=$(echo "$STATE" | jq -r '.spec_path // ""')

# Check if state is "running" or "paused"
if [[ "$BR_STATE" != "running" ]]; then
  # Not actively running - allow exit
  exit 0
fi

# Get transcript path from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')

if [[ -z "$TRANSCRIPT_PATH" ]] || [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  echo "⚠️  Beyond Ralph: Cannot read transcript, allowing exit" >&2
  exit 0
fi

# Check last assistant message for completion signal
if grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
  LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '
    .message.content |
    map(select(.type == "text")) |
    map(.text) |
    join("\n")
  ' 2>/dev/null || echo "")

  # Check for completion signals
  if [[ "$LAST_OUTPUT" == *"AUTOMATION_COMPLETE"* ]]; then
    echo "✅ Beyond Ralph: Project complete!"
    # Update state to complete
    echo "$STATE" | jq '.state = "complete"' > "$BR_STATE_FILE"
    exit 0
  fi

  # Check for pause signals
  if [[ "$LAST_OUTPUT" == *"PAUSED_FOR_QUOTA"* ]] || [[ "$LAST_OUTPUT" == *"QUOTA_LIMIT_REACHED"* ]]; then
    echo "⏸️  Beyond Ralph: Paused for quota"
    echo "$STATE" | jq '.state = "paused"' > "$BR_STATE_FILE"
    exit 0
  fi
fi

# Check if all tasks are complete by reading records
INCOMPLETE_TASKS=0
if [[ -d "records" ]]; then
  # Count incomplete checkboxes in task files
  INCOMPLETE_TASKS=$(grep -r '\[ \]' records/*/tasks.md 2>/dev/null | wc -l || echo "0")
fi

if [[ "$INCOMPLETE_TASKS" -eq 0 ]]; then
  echo "✅ Beyond Ralph: All tasks complete!"
  echo "$STATE" | jq '.state = "complete"' > "$BR_STATE_FILE"
  exit 0
fi

# Not complete - continue working
# Update last activity timestamp
UPDATED_STATE=$(echo "$STATE" | jq --arg ts "$(date -Iseconds)" '.last_activity = $ts')
echo "$UPDATED_STATE" > "$BR_STATE_FILE"

# Build the continuation prompt
PROMPT="You are the Beyond Ralph Orchestrator. CONTINUE WORKING.

Current state:
- Phase: $BR_PHASE
- Spec: $SPEC_PATH
- Incomplete tasks: $INCOMPLETE_TASKS

DO NOT STOP. Continue executing the current phase.
Check PROJECT_PLAN.md and records/*/tasks.md for what needs to be done.
Work through phases until ALL tasks have 6/6 checkboxes.

Output AUTOMATION_COMPLETE only when truly complete."

# Output JSON to block the stop and feed prompt back
jq -n \
  --arg prompt "$PROMPT" \
  --arg msg "🔄 Beyond Ralph continuing... Phase: $BR_PHASE | $INCOMPLETE_TASKS tasks remaining" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
