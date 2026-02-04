# Module 5.2: Hooks - Specification

> Claude Code Hooks: Event handlers for persistence and quota management.

---

## Overview

Hooks provide event handlers that integrate with Claude Code's hook system. They enable ralph-loop persistence, quota checking before agent spawning, and subagent result handling.

**Key Principle**: Hooks are lightweight event handlers that modify Claude Code behavior.

---

## Location

- `.claude/hooks/*.yaml` - Hook definitions
- `src/beyond_ralph/hooks/` - Hook implementations

---

## Components

### 5.2.1 Stop Hook (`stop.yaml` / `stop_handler.py`)

**Purpose**: Keep orchestrator running until project is complete.

**Hook Definition** (`.claude/hooks/stop.yaml`):
```yaml
name: beyond-ralph-stop
description: "Keep Beyond Ralph running until project complete"
event: on_stop
handler: src/beyond_ralph/hooks/stop_handler.py

# Conditions for hook to fire
conditions:
  - env: BEYOND_RALPH_ACTIVE
    value: "true"
```

**Handler Implementation**:
```python
from beyond_ralph.core.orchestrator import Orchestrator

def handle_stop() -> dict:
    """Handle stop event.

    Returns:
        {
            "continue": True/False,
            "message": "Reason for continuing or stopping"
        }

    Logic:
        1. Check if orchestrator is active
        2. Check if project is complete
        3. If not complete, return continue=True
        4. If complete or error, return continue=False
    """
    orchestrator = Orchestrator.get_instance()

    if orchestrator is None:
        return {"continue": False, "message": "No active orchestrator"}

    if orchestrator.is_complete():
        return {"continue": False, "message": "Project complete!"}

    if orchestrator.has_fatal_error():
        return {"continue": False, "message": f"Fatal error: {orchestrator.error}"}

    # Continue running
    return {"continue": True, "message": "Project in progress, continuing..."}
```

---

### 5.2.2 Quota Check Hook (`quota-check.yaml` / `quota_check.py`)

**Purpose**: Check quota before spawning agents via Task tool.

**Hook Definition** (`.claude/hooks/quota-check.yaml`):
```yaml
name: beyond-ralph-quota-check
description: "Check quota before spawning agents"
event: pre_tool_use
tools:
  - Task
handler: src/beyond_ralph/hooks/quota_check.py
```

**Handler Implementation**:
```python
from beyond_ralph.core.quota_manager import QuotaManager

def handle_pre_tool_use(tool_name: str, tool_args: dict) -> dict:
    """Handle pre-tool-use event for Task tool.

    Args:
        tool_name: Name of tool being called (always "Task" for this hook).
        tool_args: Arguments being passed to the tool.

    Returns:
        {
            "allow": True/False,
            "message": "Reason for allowing or blocking"
        }

    Logic:
        1. Check current quota status
        2. If quota >= 85%, block and return message
        3. If quota unknown, block (never fake results)
        4. Otherwise allow
    """
    quota_manager = QuotaManager()
    status = quota_manager.check()

    if status.is_unknown:
        return {
            "allow": False,
            "message": "Cannot determine quota status. Blocking to avoid overage."
        }

    if status.is_limited:
        return {
            "allow": False,
            "message": f"Quota at {max(status.session_percent, status.weekly_percent)}%. "
                       f"Waiting for reset."
        }

    return {
        "allow": True,
        "message": f"Quota OK: {status.session_percent}% session, {status.weekly_percent}% weekly"
    }
```

---

### 5.2.3 Subagent Stop Hook (`subagent-stop.yaml` / `subagent_stop.py`)

**Purpose**: Handle subagent completion and route results.

**Hook Definition** (`.claude/hooks/subagent-stop.yaml`):
```yaml
name: beyond-ralph-subagent-stop
description: "Handle subagent completion"
event: on_subagent_complete
handler: src/beyond_ralph/hooks/subagent_stop.py
```

**Handler Implementation**:
```python
from beyond_ralph.core.orchestrator import Orchestrator

def handle_subagent_complete(
    session_id: str,
    result: str,
    success: bool
) -> dict:
    """Handle subagent completion.

    Args:
        session_id: UUID of completed session.
        result: Final result from session.
        success: Whether session completed successfully.

    Returns:
        {
            "acknowledged": True,
            "next_action": "continue" | "pause" | "complete"
        }

    Logic:
        1. Get orchestrator instance
        2. Route result to appropriate phase handler
        3. Determine next action based on result
    """
    orchestrator = Orchestrator.get_instance()

    if orchestrator is None:
        return {"acknowledged": True, "next_action": "pause"}

    # Route result to orchestrator
    orchestrator.handle_agent_result(session_id, result, success)

    # Determine next action
    if orchestrator.is_complete():
        return {"acknowledged": True, "next_action": "complete"}

    if orchestrator.is_paused():
        return {"acknowledged": True, "next_action": "pause"}

    return {"acknowledged": True, "next_action": "continue"}
```

---

## Hook Events Reference

| Event | When Fired | Handler Returns |
|-------|------------|-----------------|
| `on_stop` | User tries to stop Claude | `{continue: bool, message: str}` |
| `pre_tool_use` | Before tool execution | `{allow: bool, message: str}` |
| `on_subagent_complete` | Subagent finishes | `{acknowledged: bool, next_action: str}` |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `BEYOND_RALPH_ACTIVE` | Set to "true" when orchestrator is running |
| `BEYOND_RALPH_SESSION_ID` | Current orchestrator session ID |
| `BEYOND_RALPH_PHASE` | Current phase number |

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 1.1 (Orchestrator) | State checking |
| Module 1.3 (Quota Manager) | Quota checking |

---

## Error Handling

Hooks should be resilient:
- Catch all exceptions
- Return safe defaults on error
- Log errors for debugging
- Never crash Claude Code

```python
def safe_hook_handler(func):
    """Decorator for safe hook handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Hook error: {e}")
            # Return safe default
            return {"continue": False, "message": f"Hook error: {e}"}
    return wrapper
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Handler logic |
| Integration tests | Hook + orchestrator |
| Live tests | Real Claude Code hooks |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
