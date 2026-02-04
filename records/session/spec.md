# Module 1.2: Session Manager - Specification

> Session Management: Spawn and communicate with Claude Code sessions.

---

## Overview

The Session Manager handles spawning new Claude Code sessions via CLI or Task tool, sending messages, receiving results, and managing session lifecycle. It is a core component of the Core module.

**Key Principle**: Sessions are isolated contexts that stream output back to the orchestrator.

---

## Location

`src/beyond_ralph/core/session_manager.py`

---

## Components

### Session Manager Class

**Purpose**: Manage Claude Code session spawning and communication.

**Interface**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Callable

@dataclass
class SessionOutput:
    """Output from a session message."""
    text: str
    session_id: str
    timestamp: datetime

    def formatted(self) -> str:
        """Return output with [AGENT:session_id] prefix.

        Example: [AGENT:br-d35605c9] Starting implementation...
        """
        return f"[AGENT:{self.session_id}] {self.text}"

@dataclass
class Session:
    """Represents an active Claude Code session."""
    session_id: str
    created_at: datetime
    status: Literal["running", "complete", "failed"]

    async def send(self, message: str) -> SessionOutput:
        """Send message to session.

        Uses --continue flag to continue existing session.
        """

    async def complete(self) -> "AgentResult":
        """Wait for session to complete and get final result.

        Blocks until session finishes.
        """

    async def get_result(self) -> "AgentResult":
        """Get result without waiting.

        For already-completed sessions.
        """

    async def cleanup(self) -> None:
        """Clean up session resources.

        Releases lock file, cleans temp files.
        """

class SessionManager:
    """Manages Claude Code session spawning and communication."""

    def __init__(self, safemode: bool = False) -> None:
        """Initialize session manager.

        Args:
            safemode: If False (default), use --dangerously-skip-permissions.
        """
        self.safemode = safemode
        self.active_sessions: dict[str, Session] = {}
        self.lock_dir = Path(".beyond_ralph_sessions/locks/")

    def spawn(
        self,
        prompt: str,
        use_cli: bool = False,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> Session:
        """Spawn a new Claude Code session.

        Args:
            prompt: Initial prompt for the session.
            use_cli: If True, spawn via CLI subprocess.
                     If False, use Claude Code Task tool.
            output_callback: Callback for streaming output line-by-line.

        Returns:
            Session object for further interaction.

        Raises:
            SessionSpawnError: If spawning fails.
            QuotaError: If quota is exceeded.

        Flow:
            1. Check quota before spawning
            2. Generate unique session ID
            3. Acquire lock for session ID
            4. Spawn session via chosen method
            5. Stream output via callback
            6. Return Session object
        """

    def spawn_cli(self, prompt: str) -> Session:
        """Spawn session via CLI subprocess.

        Uses pexpect to interact with claude CLI.

        Command:
            claude --dangerously-skip-permissions -p "{prompt}"
            (or without flag if safemode=True)
        """

    def is_locked(self, session_id: str) -> bool:
        """Check if session is locked by another process.

        Uses lock files with PID to prevent concurrent access.
        Stale locks (PID not running) are automatically cleaned.
        """

    def _acquire_lock(self, session_id: str) -> None:
        """Acquire lock for session ID."""

    def _release_lock(self, session_id: str) -> None:
        """Release lock for session ID."""

    def _extract_result(self, output: str) -> str:
        """Extract final result from session output.

        Returns the RESULT, not the work being done.
        Looks for conclusion/summary patterns in output.
        """

    def get_active_sessions(self) -> list[Session]:
        """Get all currently active sessions."""

    def cleanup_all(self) -> None:
        """Clean up all sessions."""
```

---

## Lock File Format

Lock files stored in `.beyond_ralph_sessions/locks/`:

```
# .beyond_ralph_sessions/locks/br-d35605c9.lock
pid: 12345
created: 2026-02-02T00:49:45
```

---

## Output Streaming

Sessions stream output line-by-line to the orchestrator:

```
[AGENT:br-d35605c9] Reading specification file...
[AGENT:br-d35605c9] Found 5 major features
[AGENT:br-d35605c9] Preparing interview questions
[BEYOND-RALPH] Phase 1 complete, transitioning to Phase 2
```

---

## CLI Spawning Details

When `use_cli=True`:

1. **Spawn Process**:
   ```bash
   claude --dangerously-skip-permissions -p "prompt here"
   ```

2. **Continue Session**:
   ```bash
   claude --continue br-d35605c9 -p "follow-up message"
   ```

3. **Parse Output**:
   - Stream stdout/stderr to callback
   - Detect completion patterns
   - Extract final result

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 12 (Utils) | UUID generation, logging |
| Module 1.3 (Quota Manager) | Pre-spawn quota check |

---

## Error Handling

```python
class SessionError(BeyondRalphError):
    """Session-related errors."""

class SessionSpawnError(SessionError):
    """Failed to spawn session."""

class SessionTimeoutError(SessionError):
    """Session execution timed out."""

class SessionLockError(SessionError):
    """Failed to acquire session lock."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Lock management, result extraction |
| Integration tests | Session spawning with mocks |
| Live tests | Real Claude CLI sessions |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
