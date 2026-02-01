# Module 5: Session Management - Specification

**Module**: session
**Location**: `src/beyond_ralph/core/session_manager.py`
**Dependencies**: None (foundational)

## Purpose

Spawn and control Claude Code sessions via CLI, enabling multi-agent coordination.

## Requirements

### R1: Session Spawning
- Start new Claude Code sessions via CLI
- Return UUID of new session
- Use `--dangerously-skip-permissions` by default
- Support `safemode` config to require permissions

### R2: Session Communication
- Send requests to sessions by UUID
- Return final human-readable result (the RESULT, not work logs)
- Support follow-up messages
- Loop until work complete

### R3: Session Locking
- Check no other Claude process using same UUID before interaction
- Prevent concurrent access to same session
- Use file-based or process-based locking

### R4: Session Cleanup
- Clean up completed sessions
- Handle orphaned sessions
- Maintain session registry

## Interface

```python
class SessionManager:
    async def spawn(
        self,
        prompt: str,
        agent_type: str,
        safemode: bool = False,
    ) -> SessionInfo

    async def send(self, session_id: str, message: str) -> str

    async def is_locked(self, session_id: str) -> bool

    async def cleanup(self, session_id: str) -> None

    async def list_active(self) -> list[SessionInfo]
```

## Testing Requirements

- Mock CLI interactions for unit tests
- Test locking behavior
- Test cleanup
- Integration test with real Claude Code (live test)
