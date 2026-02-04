# Module 5: Skills & Hooks - Specification

> Claude Code Integration: Skills for user commands and hooks for autonomous operation.

---

## Overview

The Skills & Hooks module provides the native Claude Code integration layer. Skills enable users to invoke Beyond Ralph via `/beyond-ralph` commands. Hooks enable autonomous operation by preventing Claude from stopping and checking quotas before operations.

**Key Principle**: Beyond Ralph runs INSIDE Claude Code, not as an external tool.

---

## Components

### 5.1 Skills (`skills/`)

**Location**:
- `.claude/skills/` (YAML definitions)
- `src/beyond_ralph/skills/` (Python handlers)

### 5.2 Hooks (`hooks/`)

**Location**:
- `.claude/hooks/` (YAML definitions)
- `src/beyond_ralph/hooks/` (Python handlers)

---

## Skills

### `/beyond-ralph:start`

**File**: `.claude/skills/beyond-ralph.yaml`

```yaml
name: beyond-ralph:start
description: Start a new Beyond Ralph autonomous development project
usage: /beyond-ralph:start --spec <path>
parameters:
  spec:
    type: string
    required: true
    description: Path to the project specification file
instructions: |
  Start the Beyond Ralph orchestrator with the given specification.
  This will:
  1. Ingest the specification (Phase 1)
  2. Interview the user deeply (Phase 2)
  3. Create modular spec and project plan (Phases 3-4)
  4. Validate and iterate until complete (Phases 5-6)
  5. Implement with TDD and three-agent trust model (Phase 7)
  6. Test and verify (Phase 8)

  ALL subagent activity streams to this session.
  User sees [BEYOND-RALPH] and [AGENT:xyz] prefixed messages.
```

**Handler**: `src/beyond_ralph/skills/__init__.py`

```python
async def handle_start(spec_path: str) -> None:
    """Handle /beyond-ralph:start command.

    Args:
        spec_path: Path to specification file.

    Flow:
        1. Validate spec file exists
        2. Initialize orchestrator
        3. Start phase 1
        4. Stream all output to session
    """
```

### `/beyond-ralph:resume`

**File**: `.claude/skills/beyond-ralph-resume.yaml`

```yaml
name: beyond-ralph:resume
description: Resume a paused Beyond Ralph project
usage: /beyond-ralph:resume
instructions: |
  Resume the most recently paused Beyond Ralph project.
  Loads saved state from .beyond_ralph_sessions/
  Continues from last checkpoint.
```

**Handler**:
```python
async def handle_resume() -> None:
    """Handle /beyond-ralph:resume command.

    Flow:
        1. Find most recent session in .beyond_ralph_sessions/
        2. Load saved state
        3. Check quota before resuming
        4. Continue from checkpoint
    """
```

### `/beyond-ralph:status`

**File**: `.claude/skills/beyond-ralph-status.yaml`

```yaml
name: beyond-ralph:status
description: Show current Beyond Ralph project status
usage: /beyond-ralph:status
instructions: |
  Display current status including:
  - Current phase
  - Active agents
  - Task completion summary
  - Quota usage
```

**Handler**:
```python
def handle_status() -> OrchestratorStatus:
    """Handle /beyond-ralph:status command.

    Returns:
        OrchestratorStatus with full project state.
    """
```

### `/beyond-ralph:pause`

**File**: `.claude/skills/beyond-ralph-pause.yaml`

```yaml
name: beyond-ralph:pause
description: Manually pause the current Beyond Ralph project
usage: /beyond-ralph:pause
instructions: |
  Pause the current project.
  State is saved to .beyond_ralph_sessions/
  Resume later with /beyond-ralph:resume
```

**Handler**:
```python
async def handle_pause() -> None:
    """Handle /beyond-ralph:pause command.

    Flow:
        1. Signal orchestrator to pause
        2. Save current state
        3. Stop spawning new agents
        4. Allow running agents to complete
    """
```

---

## Hooks

### Stop Hook

**File**: `.claude/hooks/stop.yaml`

```yaml
name: beyond-ralph-stop
description: Prevent Claude from stopping while Beyond Ralph is running
event: Stop
match: "*"
action: prevent
condition: |
  Check if Beyond Ralph orchestrator is active.
  If active and project not complete, prevent stop.
  Return continue=true to keep running.
handler: src/beyond_ralph/hooks/stop_handler.py
```

**Handler**: `src/beyond_ralph/hooks/stop_handler.py`

```python
from beyond_ralph.core.orchestrator import Orchestrator

def stop_hook_handler(reason: str) -> HookResponse:
    """Handle stop hook.

    Args:
        reason: Why Claude wants to stop.

    Returns:
        HookResponse with continue=True if project not complete.
    """
    orchestrator = Orchestrator.get_active()
    if orchestrator and not orchestrator.is_complete():
        return HookResponse(
            continue_=True,
            message="[BEYOND-RALPH] Project not complete, continuing..."
        )
    return HookResponse(continue_=False)

@dataclass
class HookResponse:
    continue_: bool  # True to prevent stop
    message: Optional[str] = None
```

### Quota Check Hook

**File**: `.claude/hooks/quota-check.yaml`

```yaml
name: beyond-ralph-quota-check
description: Check quota before agent operations
event: PreToolUse
match: "Task"  # Before spawning agents
handler: src/beyond_ralph/hooks/quota_check.py
```

**Handler**: `src/beyond_ralph/hooks/quota_check.py`

```python
from beyond_ralph.core.quota_manager import QuotaManager

def quota_hook_handler() -> HookResponse:
    """Check quota before agent spawn.

    Returns:
        HookResponse with continue=False if quota exceeded.
    """
    quota = QuotaManager()
    status = quota.check()

    if status.is_unknown:
        return HookResponse(
            continue_=False,
            message="[BEYOND-RALPH] Cannot determine quota status, pausing."
        )

    if status.is_limited:
        return HookResponse(
            continue_=False,
            message=f"[BEYOND-RALPH] Quota at {status.session_percent}%/{status.weekly_percent}%, pausing until reset."
        )

    return HookResponse(continue_=True)
```

### Subagent Stop Hook

**File**: `.claude/hooks/subagent-stop.yaml`

```yaml
name: beyond-ralph-subagent-stop
description: Handle subagent completion
event: SubagentStop
handler: src/beyond_ralph/hooks/subagent_stop.py
```

**Handler**: `src/beyond_ralph/hooks/subagent_stop.py`

```python
def subagent_stop_handler(session_id: str, result: str) -> HookResponse:
    """Handle when a subagent stops.

    Args:
        session_id: UUID of the stopped session.
        result: Final output from the session.

    Returns:
        HookResponse indicating handling complete.
    """
    # Parse agent result
    agent_result = AgentResult.from_session_output(result)

    # Store in session manager
    session_manager = SessionManager.get_instance()
    session_manager.record_result(session_id, agent_result)

    # Log completion
    print(f"[BEYOND-RALPH] Agent {session_id} completed")

    return HookResponse(continue_=True)
```

---

## Skill/Hook Data Types

```python
@dataclass
class SkillInvocation:
    """A skill invocation from the user."""
    skill_name: str
    arguments: dict[str, Any]
    session_id: str

@dataclass
class HookEvent:
    """An event that triggered a hook."""
    event_type: Literal["Stop", "PreToolUse", "SubagentStop"]
    payload: dict[str, Any]
    timestamp: datetime

@dataclass
class HookResponse:
    """Response from a hook handler."""
    continue_: bool  # Whether to allow the operation
    message: Optional[str] = None  # Message to display
    data: Optional[dict] = None  # Additional data
```

---

## Entry Points

**File**: `pyproject.toml`

```toml
[project.scripts]
br-start = "beyond_ralph.cli:start_command"
br-resume = "beyond_ralph.cli:resume_command"
br-status = "beyond_ralph.cli:status_command"
br-pause = "beyond_ralph.cli:pause_command"
br-quota = "beyond_ralph.utils.quota_checker:main"
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 1 (Core) | Invoking orchestrator |
| Module 4 (Records) | Displaying status |

---

## Error Handling

```python
class SkillError(BeyondRalphError):
    """Skill execution errors."""

class HookError(BeyondRalphError):
    """Hook execution errors."""

class InvalidSkillError(SkillError):
    """Invalid skill or arguments."""

class HookPreventedError(HookError):
    """Operation prevented by hook."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Skill argument parsing, hook logic |
| Integration tests | YAML loading, handler invocation |
| Live tests | Full Claude Code integration |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (100% coverage)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
