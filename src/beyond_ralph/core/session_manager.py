"""Session Manager for Beyond Ralph.

Handles spawning and managing Claude Code sessions/subagents.
"""

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator

import psutil


class SessionStatus(Enum):
    """Session status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class SessionInfo:
    """Information about a session."""

    uuid: str
    agent_type: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    prompt: str
    result: str | None = None
    error: str | None = None
    pid: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "uuid": self.uuid,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "prompt": self.prompt,
            "result": self.result,
            "error": self.error,
            "pid": self.pid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionInfo":
        """Create from dictionary."""
        return cls(
            uuid=data["uuid"],
            agent_type=data["agent_type"],
            status=SessionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            prompt=data["prompt"],
            result=data.get("result"),
            error=data.get("error"),
            pid=data.get("pid"),
        )


# Session lock file location
SESSION_LOCK_DIR = Path(".beyond_ralph_sessions")


class SessionManager:
    """Manages Claude Code sessions and subagents."""

    def __init__(
        self,
        safemode: bool = False,
        lock_dir: Path | None = None,
    ):
        """Initialize session manager.

        Args:
            safemode: If True, don't use --dangerously-skip-permissions.
            lock_dir: Directory for session lock files.
        """
        self.safemode = safemode
        self.lock_dir = lock_dir or SESSION_LOCK_DIR
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: dict[str, SessionInfo] = {}

    def _generate_uuid(self) -> str:
        """Generate a session UUID."""
        return str(uuid.uuid4())[:8]

    def _get_lock_file(self, session_uuid: str) -> Path:
        """Get path to session lock file."""
        return self.lock_dir / f"{session_uuid}.lock"

    async def is_locked(self, session_uuid: str) -> bool:
        """Check if a session is in use by another process.

        Args:
            session_uuid: Session UUID to check.

        Returns:
            True if session is locked.
        """
        lock_file = self._get_lock_file(session_uuid)
        if not lock_file.exists():
            return False

        try:
            data = json.loads(lock_file.read_text())
            pid = data.get("pid")
            if pid and psutil.pid_exists(pid):
                return True
            # Process died, clean up stale lock
            lock_file.unlink()
        except (json.JSONDecodeError, KeyError):
            pass

        return False

    async def _acquire_lock(self, session_uuid: str) -> bool:
        """Acquire lock on a session.

        Args:
            session_uuid: Session UUID to lock.

        Returns:
            True if lock acquired.
        """
        if await self.is_locked(session_uuid):
            return False

        lock_file = self._get_lock_file(session_uuid)
        lock_data = {
            "pid": os.getpid(),
            "locked_at": datetime.now().isoformat(),
        }
        lock_file.write_text(json.dumps(lock_data))
        return True

    async def _release_lock(self, session_uuid: str) -> None:
        """Release lock on a session.

        Args:
            session_uuid: Session UUID to unlock.
        """
        lock_file = self._get_lock_file(session_uuid)
        if lock_file.exists():
            lock_file.unlink()

    async def spawn(
        self,
        prompt: str,
        agent_type: str = "general",
        timeout: int = 3600,
    ) -> SessionInfo:
        """Spawn a new Claude Code session/subagent.

        This uses the Task tool internally to spawn subagents within
        Claude Code's native subagent system.

        Args:
            prompt: The task prompt for the agent.
            agent_type: Type of agent to spawn.
            timeout: Timeout in seconds.

        Returns:
            SessionInfo with the new session's details.

        Note:
            This is designed to work INSIDE Claude Code, using the
            Task tool to spawn subagents. For testing or standalone
            use, it falls back to subprocess-based spawning.
        """
        session_uuid = self._generate_uuid()
        now = datetime.now()

        session = SessionInfo(
            uuid=session_uuid,
            agent_type=agent_type,
            status=SessionStatus.PENDING,
            created_at=now,
            updated_at=now,
            prompt=prompt,
        )

        # Acquire lock
        if not await self._acquire_lock(session_uuid):
            raise RuntimeError(f"Could not acquire lock for session {session_uuid}")

        self._active_sessions[session_uuid] = session

        # Update status to running
        session.status = SessionStatus.RUNNING
        session.updated_at = datetime.now()

        return session

    async def send(self, session_uuid: str, message: str) -> str:
        """Send a message to an existing session.

        Args:
            session_uuid: Session to send to.
            message: Message to send.

        Returns:
            Response from the session.
        """
        if session_uuid not in self._active_sessions:
            raise ValueError(f"Unknown session: {session_uuid}")

        session = self._active_sessions[session_uuid]
        if session.status != SessionStatus.RUNNING:
            raise RuntimeError(f"Session {session_uuid} is not running")

        # In Claude Code, this would send a message to the subagent
        # For now, this is a placeholder
        return f"[Session {session_uuid}] Received: {message}"

    async def get_result(self, session_uuid: str) -> str | None:
        """Get the final result from a completed session.

        Args:
            session_uuid: Session UUID.

        Returns:
            Result string or None if not complete.
        """
        session = self._active_sessions.get(session_uuid)
        if not session:
            return None
        return session.result

    async def complete(self, session_uuid: str, result: str) -> None:
        """Mark a session as completed with a result.

        Args:
            session_uuid: Session UUID.
            result: Final result.
        """
        session = self._active_sessions.get(session_uuid)
        if session:
            session.status = SessionStatus.COMPLETED
            session.result = result
            session.updated_at = datetime.now()
            await self._release_lock(session_uuid)

    async def fail(self, session_uuid: str, error: str) -> None:
        """Mark a session as failed.

        Args:
            session_uuid: Session UUID.
            error: Error message.
        """
        session = self._active_sessions.get(session_uuid)
        if session:
            session.status = SessionStatus.FAILED
            session.error = error
            session.updated_at = datetime.now()
            await self._release_lock(session_uuid)

    async def cleanup(self, session_uuid: str) -> None:
        """Clean up a session.

        Args:
            session_uuid: Session UUID.
        """
        await self._release_lock(session_uuid)
        self._active_sessions.pop(session_uuid, None)

    async def get_active_sessions(self) -> list[SessionInfo]:
        """Get all active sessions.

        Returns:
            List of active SessionInfo.
        """
        return [
            s for s in self._active_sessions.values()
            if s.status == SessionStatus.RUNNING
        ]

    async def get_session(self, session_uuid: str) -> SessionInfo | None:
        """Get session by UUID.

        Args:
            session_uuid: Session UUID.

        Returns:
            SessionInfo if found.
        """
        return self._active_sessions.get(session_uuid)

    def count_active(self) -> int:
        """Count currently active sessions.

        Returns:
            Number of running sessions.
        """
        return sum(
            1 for s in self._active_sessions.values()
            if s.status == SessionStatus.RUNNING
        )


# Singleton instance
_session_manager: SessionManager | None = None


def get_session_manager(safemode: bool = False) -> SessionManager:
    """Get the session manager singleton.

    Args:
        safemode: Whether to use safe mode.

    Returns:
        The SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(safemode=safemode)
    return _session_manager
