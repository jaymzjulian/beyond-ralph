"""Unit tests for Session Manager."""

from pathlib import Path

import pytest

from beyond_ralph.core.session_manager import (
    SessionInfo,
    SessionManager,
    SessionStatus,
)


@pytest.fixture
def temp_lock_dir(tmp_path: Path) -> Path:
    """Create a temporary lock directory."""
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    return lock_dir


@pytest.fixture
def session_manager(temp_lock_dir: Path) -> SessionManager:
    """Create a session manager with temp lock directory."""
    return SessionManager(lock_dir=temp_lock_dir)


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_spawn_session(self, session_manager: SessionManager) -> None:
        """Test spawning a new session."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
        )

        assert session.uuid
        assert session.agent_type == "test"
        assert session.status == SessionStatus.RUNNING
        assert session.prompt == "Test task"

    @pytest.mark.asyncio
    async def test_session_locking(self, session_manager: SessionManager) -> None:
        """Test session locking prevents duplicate access."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
        )

        # Session should be locked
        is_locked = await session_manager.is_locked(session.uuid)
        assert is_locked

    @pytest.mark.asyncio
    async def test_complete_session(self, session_manager: SessionManager) -> None:
        """Test completing a session."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
        )

        await session_manager.complete(session.uuid, "Task completed successfully")

        retrieved = await session_manager.get_session(session.uuid)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.COMPLETED
        assert retrieved.result == "Task completed successfully"

        # Lock should be released
        is_locked = await session_manager.is_locked(session.uuid)
        assert not is_locked

    @pytest.mark.asyncio
    async def test_fail_session(self, session_manager: SessionManager) -> None:
        """Test failing a session."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
        )

        await session_manager.fail(session.uuid, "Something went wrong")

        retrieved = await session_manager.get_session(session.uuid)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.FAILED
        assert retrieved.error == "Something went wrong"

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_manager: SessionManager) -> None:
        """Test getting active sessions."""
        session1 = await session_manager.spawn(prompt="Task 1", agent_type="test")
        session2 = await session_manager.spawn(prompt="Task 2", agent_type="test")

        active = await session_manager.get_active_sessions()
        assert len(active) == 2

        # Complete one
        await session_manager.complete(session1.uuid, "Done")

        active = await session_manager.get_active_sessions()
        assert len(active) == 1
        assert active[0].uuid == session2.uuid

    @pytest.mark.asyncio
    async def test_count_active(self, session_manager: SessionManager) -> None:
        """Test counting active sessions."""
        assert session_manager.count_active() == 0

        await session_manager.spawn(prompt="Task 1", agent_type="test")
        assert session_manager.count_active() == 1

        await session_manager.spawn(prompt="Task 2", agent_type="test")
        assert session_manager.count_active() == 2

    @pytest.mark.asyncio
    async def test_cleanup(self, session_manager: SessionManager) -> None:
        """Test session cleanup."""
        session = await session_manager.spawn(prompt="Task", agent_type="test")

        await session_manager.cleanup(session.uuid)

        retrieved = await session_manager.get_session(session.uuid)
        assert retrieved is None

        is_locked = await session_manager.is_locked(session.uuid)
        assert not is_locked


class TestSessionInfo:
    """Tests for SessionInfo."""

    def test_to_dict(self) -> None:
        """Test converting session info to dict."""
        from datetime import datetime

        session = SessionInfo(
            uuid="test-123",
            agent_type="implementation",
            status=SessionStatus.RUNNING,
            created_at=datetime(2024, 2, 1, 10, 0),
            updated_at=datetime(2024, 2, 1, 10, 30),
            prompt="Implement feature",
        )

        data = session.to_dict()

        assert data["uuid"] == "test-123"
        assert data["agent_type"] == "implementation"
        assert data["status"] == "running"
        assert data["prompt"] == "Implement feature"

    def test_from_dict(self) -> None:
        """Test creating session info from dict."""
        data = {
            "uuid": "test-456",
            "agent_type": "testing",
            "status": "completed",
            "created_at": "2024-02-01T10:00:00",
            "updated_at": "2024-02-01T11:00:00",
            "prompt": "Run tests",
            "result": "All tests passed",
        }

        session = SessionInfo.from_dict(data)

        assert session.uuid == "test-456"
        assert session.agent_type == "testing"
        assert session.status == SessionStatus.COMPLETED
        assert session.result == "All tests passed"
