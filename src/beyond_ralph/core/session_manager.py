"""Session Manager for Beyond Ralph.

Handles spawning and managing Claude Code sessions/subagents.

Two modes of operation:
1. CLI Mode: Spawn `claude` CLI processes (for external orchestration)
2. Task Mode: Use Claude Code's native Task tool (when running inside Claude Code)

CRITICAL: Never fake results. If a session fails, report failure.
"""

import json
import logging
import os
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    PEXPECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    UNKNOWN = "unknown"  # For never-fake-results principle


@dataclass
class SessionOutput:
    """Output from a session with streaming support."""

    session_uuid: str
    line: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_final: bool = False
    is_error: bool = False

    def formatted(self) -> str:
        """Format output with agent prefix."""
        prefix = f"[AGENT:{self.session_uuid}]"
        if self.is_error:
            prefix = f"[AGENT:{self.session_uuid}:ERROR]"
        return f"{prefix} {self.line}"


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

    def _find_claude_cli(self) -> str | None:
        """Find the Claude CLI executable.

        Returns:
            Path to claude CLI or None if not found.
        """
        # Check common locations
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path

        # Check npm global installs
        npm_global = Path.home() / ".npm-global" / "bin" / "claude"
        if npm_global.exists():
            return str(npm_global)

        return None

    async def spawn_cli(
        self,
        prompt: str,
        agent_type: str = "general",
        timeout: int = 3600,
        max_turns: int = 25,
        output_callback: Callable[[SessionOutput], None] | None = None,
        working_dir: Path | None = None,
    ) -> SessionInfo:
        """Spawn a new Claude Code CLI session.

        Uses pexpect to interact with the `claude` CLI for standalone
        orchestration (external to Claude Code).

        Args:
            prompt: The task prompt for the agent.
            agent_type: Type of agent to spawn.
            timeout: Timeout in seconds.
            max_turns: Maximum agentic turns before stopping (prevents context exhaustion).
            output_callback: Callback for streaming output (for [AGENT:id] prefixing).
            working_dir: Working directory for the session.

        Returns:
            SessionInfo with the session's details including final result.

        Raises:
            RuntimeError: If Claude CLI not found or pexpect not available.
        """
        if not PEXPECT_AVAILABLE:
            raise RuntimeError(
                "pexpect is required for CLI session spawning. "
                "Install with: uv add pexpect"
            )

        claude_path = self._find_claude_cli()
        if not claude_path:
            raise RuntimeError(
                "Claude CLI not found. Ensure it's installed and in PATH."
            )

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

        try:
            # Build command
            cmd_args = [claude_path]
            if not self.safemode:
                cmd_args.append("--dangerously-skip-permissions")
            if max_turns > 0:
                cmd_args.extend(["--max-turns", str(max_turns)])
            cmd_args.extend(["-p", prompt])

            logger.info(f"[BEYOND-RALPH] Spawning session {session_uuid} ({agent_type})")

            # Spawn the process
            cwd = str(working_dir) if working_dir else None
            child = pexpect.spawn(
                cmd_args[0],
                cmd_args[1:],
                timeout=timeout,
                encoding="utf-8",
                cwd=cwd,
            )

            session.status = SessionStatus.RUNNING
            session.pid = child.pid
            session.updated_at = datetime.now()

            # Collect output
            output_lines: list[str] = []

            def emit_output(line: str, is_error: bool = False) -> None:
                """Emit output line with callback."""
                output = SessionOutput(
                    session_uuid=session_uuid,
                    line=line,
                    is_error=is_error,
                )
                output_lines.append(line)
                if output_callback:
                    output_callback(output)

            # Read output until completion
            while True:
                try:
                    # Read a line
                    index = child.expect(["\r\n", "\n", pexpect.EOF, pexpect.TIMEOUT], timeout=30)

                    if index in (0, 1):  # Got a line
                        line = child.before.strip()
                        if line:
                            emit_output(line)
                    elif index == 2:  # EOF - process completed
                        # Get any remaining output
                        remaining = child.before.strip()
                        if remaining:
                            for line in remaining.split("\n"):
                                if line.strip():
                                    emit_output(line.strip())
                        break
                    elif index == 3:  # Timeout - check if still running
                        if not child.isalive():
                            break
                        # Still running, continue waiting

                except pexpect.exceptions.EOF:
                    break
                except pexpect.exceptions.TIMEOUT:
                    if not child.isalive():
                        break

            # Get exit status
            child.close()
            exit_code = child.exitstatus or 0

            if exit_code == 0:
                session.status = SessionStatus.COMPLETED
                # Extract the final result (last meaningful output)
                session.result = self._extract_result(output_lines)
                logger.info(f"[BEYOND-RALPH] Session {session_uuid} completed successfully")
            else:
                session.status = SessionStatus.FAILED
                session.error = f"Exit code: {exit_code}"
                session.result = "\n".join(output_lines[-10:])  # Last 10 lines for debugging
                logger.error(f"[BEYOND-RALPH] Session {session_uuid} failed: {session.error}")

        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error = str(e)
            logger.error(f"[BEYOND-RALPH] Session {session_uuid} error: {e}")
            # NEVER fake results - report actual failure
            raise

        finally:
            session.updated_at = datetime.now()
            await self._release_lock(session_uuid)

        return session

    def _extract_result(self, output_lines: list[str]) -> str:
        """Extract the meaningful result from session output.

        The result is the final message from Claude, not the work being done.

        Args:
            output_lines: All output lines from the session.

        Returns:
            The extracted result string.
        """
        if not output_lines:
            return ""

        # Look for common result indicators
        result_lines: list[str] = []
        in_result = False

        for line in reversed(output_lines):
            # Skip empty lines at the end
            if not line.strip() and not result_lines:
                continue

            # Look for "done" indicators
            lower_line = line.lower()
            if any(marker in lower_line for marker in [
                "complete", "done", "finished", "result:", "summary:",
                "successfully", "implemented", "created", "fixed"
            ]):
                in_result = True

            if in_result or len(result_lines) < 5:
                result_lines.insert(0, line)

            # Stop after getting enough context
            if len(result_lines) >= 20:
                break

        return "\n".join(result_lines)

    async def spawn(
        self,
        prompt: str,
        agent_type: str = "general",
        timeout: int = 3600,
        max_turns: int = 25,
        use_cli: bool = False,
        output_callback: Callable[[SessionOutput], None] | None = None,
        working_dir: Path | None = None,
    ) -> SessionInfo:
        """Spawn a new Claude Code session/subagent.

        Two modes:
        1. Task Mode (default): For use inside Claude Code with Task tool
        2. CLI Mode (use_cli=True): For standalone orchestration via CLI

        Args:
            prompt: The task prompt for the agent.
            agent_type: Type of agent to spawn.
            timeout: Timeout in seconds.
            max_turns: Maximum agentic turns before stopping (prevents context exhaustion).
            use_cli: If True, use CLI spawning instead of Task tool.
            output_callback: Callback for streaming output.
            working_dir: Working directory for the session.

        Returns:
            SessionInfo with the new session's details.

        Note:
            When running inside Claude Code, prefer Task tool mode.
            CLI mode is for external orchestration or testing.
        """
        if use_cli:
            return await self.spawn_cli(
                prompt=prompt,
                agent_type=agent_type,
                timeout=timeout,
                max_turns=max_turns,
                output_callback=output_callback,
                working_dir=working_dir,
            )

        # Task tool mode - create session info for later execution
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

    async def send(
        self,
        session_uuid: str,
        message: str,
        use_cli: bool = False,
        output_callback: Callable[[SessionOutput], None] | None = None,
        timeout: int = 3600,
    ) -> str:
        """Send a follow-up message to an existing session.

        Uses `claude --continue` to resume a previous conversation.

        Args:
            session_uuid: Session to send to.
            message: Message to send.
            use_cli: If True, use CLI mode with --continue.
            output_callback: Callback for streaming output.
            timeout: Timeout in seconds.

        Returns:
            Response from the session.

        Raises:
            ValueError: If session not found.
            RuntimeError: If CLI not available or session not in valid state.
        """
        if session_uuid not in self._active_sessions:
            raise ValueError(f"Unknown session: {session_uuid}")

        session = self._active_sessions[session_uuid]

        if use_cli:
            return await self._send_cli(
                session_uuid=session_uuid,
                message=message,
                output_callback=output_callback,
                timeout=timeout,
            )

        # Task mode placeholder - would use Task tool resume
        if session.status not in (SessionStatus.RUNNING, SessionStatus.COMPLETED):
            raise RuntimeError(f"Session {session_uuid} is not in a valid state for follow-up")

        return f"[Session {session_uuid}] Follow-up not yet implemented in Task mode"

    async def _send_cli(
        self,
        session_uuid: str,
        message: str,
        output_callback: Callable[[SessionOutput], None] | None = None,
        timeout: int = 3600,
    ) -> str:
        """Send a follow-up message via CLI using --continue.

        Args:
            session_uuid: Session UUID (used as conversation ID).
            message: Message to send.
            output_callback: Callback for streaming output.
            timeout: Timeout in seconds.

        Returns:
            Response from the session.
        """
        if not PEXPECT_AVAILABLE:
            raise RuntimeError("pexpect required for CLI follow-up")

        claude_path = self._find_claude_cli()
        if not claude_path:
            raise RuntimeError("Claude CLI not found")

        session = self._active_sessions.get(session_uuid)
        if not session:
            raise ValueError(f"Unknown session: {session_uuid}")

        logger.info(f"[BEYOND-RALPH] Sending follow-up to session {session_uuid}")

        try:
            # Build command with --continue
            cmd_args = [claude_path]
            if not self.safemode:
                cmd_args.append("--dangerously-skip-permissions")
            cmd_args.extend(["--continue", "-p", message])

            child = pexpect.spawn(
                cmd_args[0],
                cmd_args[1:],
                timeout=timeout,
                encoding="utf-8",
            )

            # Collect output
            output_lines: list[str] = []

            while True:
                try:
                    index = child.expect(["\r\n", "\n", pexpect.EOF, pexpect.TIMEOUT], timeout=30)

                    if index in (0, 1):
                        line = child.before.strip()
                        if line:
                            output_lines.append(line)
                            if output_callback:
                                output_callback(SessionOutput(
                                    session_uuid=session_uuid,
                                    line=line,
                                ))
                    elif index == 2:
                        remaining = child.before.strip()
                        if remaining:
                            for line in remaining.split("\n"):
                                if line.strip():
                                    output_lines.append(line.strip())
                        break
                    elif index == 3:
                        if not child.isalive():
                            break

                except pexpect.exceptions.EOF:
                    break
                except pexpect.exceptions.TIMEOUT:
                    if not child.isalive():
                        break

            child.close()
            result = self._extract_result(output_lines)

            # Update session
            session.result = result
            session.updated_at = datetime.now()

            return result

        except Exception as e:
            logger.error(f"[BEYOND-RALPH] Follow-up to {session_uuid} failed: {e}")
            raise

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
