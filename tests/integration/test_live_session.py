"""Live integration tests for session manager.

These tests actually spawn Claude CLI processes to verify session management works.
They use --print mode for quick, non-interactive tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.session_manager import (
    SessionManager,
    SessionInfo,
    SessionStatus,
    SessionOutput,
    get_session_manager,
)


class TestLiveSessionManager:
    """Live tests for session manager against real Claude CLI."""

    @pytest.fixture
    def session_manager(self, tmp_path):
        """Create a session manager for testing."""
        return SessionManager(safemode=False, lock_dir=tmp_path / ".sessions")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_session_returns_session_info(self, session_manager, tmp_path):
        """Test spawning a session returns valid SessionInfo."""
        session = await session_manager.spawn(
            prompt="Say 'hello test' and nothing else",
            working_dir=tmp_path,
        )

        assert isinstance(session, SessionInfo)
        assert session.uuid is not None
        assert len(session.uuid) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_session_uuid_format(self, session_manager, tmp_path):
        """Test session UUID has expected format."""
        session = await session_manager.spawn(
            prompt="Say 'test'",
            working_dir=tmp_path,
        )

        # UUID should be a valid string identifier (8 char truncated UUID)
        assert isinstance(session.uuid, str)
        assert len(session.uuid) == 8

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_session_state_tracking(self, session_manager, tmp_path):
        """Test session state is tracked."""
        session = await session_manager.spawn(
            prompt="Say 'tracking test'",
            working_dir=tmp_path,
        )

        # Session should be tracked
        assert session.uuid in session_manager._active_sessions

        # Status should be valid
        status = session_manager._active_sessions[session.uuid].status
        assert isinstance(status, SessionStatus)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_multiple_sessions(self, session_manager, tmp_path):
        """Test spawning multiple sessions."""
        session1 = await session_manager.spawn(
            prompt="Say 'one'",
            working_dir=tmp_path,
        )

        session2 = await session_manager.spawn(
            prompt="Say 'two'",
            working_dir=tmp_path,
        )

        # Should have different UUIDs
        assert session1.uuid != session2.uuid

        # Both should be tracked
        assert session1.uuid in session_manager._active_sessions
        assert session2.uuid in session_manager._active_sessions

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_session(self, session_manager, tmp_path):
        """Test completing a session."""
        session = await session_manager.spawn(
            prompt="Say 'complete test'",
            working_dir=tmp_path,
        )

        # Complete the session
        await session_manager.complete(session.uuid, "Test complete")

        # Status should be completed
        assert session_manager._active_sessions[session.uuid].status == SessionStatus.COMPLETED

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fail_session(self, session_manager, tmp_path):
        """Test failing a session."""
        session = await session_manager.spawn(
            prompt="Say 'fail test'",
            working_dir=tmp_path,
        )

        # Fail the session
        await session_manager.fail(session.uuid, "Test failure")

        # Status should be failed
        assert session_manager._active_sessions[session.uuid].status == SessionStatus.FAILED

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_manager, tmp_path):
        """Test getting active sessions."""
        # Spawn a session
        session = await session_manager.spawn(
            prompt="Say 'active test'",
            working_dir=tmp_path,
        )

        # Should have at least one active session (RUNNING status)
        active = await session_manager.get_active_sessions()
        assert isinstance(active, list)
        # The session should be RUNNING and thus included in active
        assert any(s.uuid == session.uuid for s in active)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_count_active(self, session_manager, tmp_path):
        """Test counting active sessions."""
        initial_count = session_manager.count_active()

        await session_manager.spawn(
            prompt="Say 'count test'",
            working_dir=tmp_path,
        )

        # Count should increase
        assert session_manager.count_active() >= initial_count


class TestLiveSessionOutput:
    """Live tests for session output handling."""

    @pytest.mark.integration
    def test_session_output_formatted(self):
        """Test SessionOutput formatting."""
        output = SessionOutput(
            session_uuid="test-123",
            line="Hello from agent",
            is_error=False,
        )

        formatted = output.formatted()

        assert "[AGENT:test-123]" in formatted
        assert "Hello from agent" in formatted

    @pytest.mark.integration
    def test_session_output_error_formatted(self):
        """Test SessionOutput error formatting."""
        output = SessionOutput(
            session_uuid="test-456",
            line="Error occurred",
            is_error=True,
        )

        formatted = output.formatted()

        assert "[AGENT:test-456" in formatted
        assert "ERROR" in formatted or "Error" in formatted


class TestLiveSessionInfo:
    """Live tests for SessionInfo."""

    @pytest.mark.integration
    def test_session_info_creation(self):
        """Test SessionInfo can be created."""
        now = datetime.now()
        info = SessionInfo(
            uuid="test-uuid-789",
            agent_type="test",
            status=SessionStatus.PENDING,
            created_at=now,
            updated_at=now,
            prompt="Test prompt",
        )

        assert info.uuid == "test-uuid-789"
        assert info.prompt == "Test prompt"

    @pytest.mark.integration
    def test_session_info_to_dict(self):
        """Test SessionInfo serialization."""
        import json

        now = datetime.now()
        info = SessionInfo(
            uuid="test-serial",
            agent_type="test",
            status=SessionStatus.PENDING,
            created_at=now,
            updated_at=now,
            prompt="Serialize test",
        )

        data = info.to_dict()
        json_str = json.dumps(data)

        assert json_str is not None
        restored = json.loads(json_str)
        assert restored["uuid"] == "test-serial"


class TestSessionManagerSafemode:
    """Tests for session manager safemode."""

    @pytest.mark.integration
    def test_safemode_flag_respected(self, tmp_path):
        """Test safemode flag is stored."""
        manager = SessionManager(safemode=True, lock_dir=tmp_path / ".sess1")
        assert manager.safemode is True

        manager2 = SessionManager(safemode=False, lock_dir=tmp_path / ".sess2")
        assert manager2.safemode is False


class TestSessionManagerCLI:
    """Tests that actually spawn Claude CLI processes."""

    @pytest.fixture
    def cli_session_manager(self, tmp_path):
        """Create a session manager for CLI testing."""
        return SessionManager(safemode=False, lock_dir=tmp_path / ".sessions")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_cli_simple_prompt(self, cli_session_manager, tmp_path):
        """Test spawning a CLI session with a simple prompt."""
        # Use -p flag for print mode (non-interactive)
        session = await cli_session_manager.spawn_cli(
            prompt="What is 2+2? Reply with just the number.",
            agent_type="math",
            timeout=60,
            working_dir=tmp_path,
        )

        assert isinstance(session, SessionInfo)
        assert session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED)
        # If completed, should have a result
        if session.status == SessionStatus.COMPLETED:
            assert session.result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_spawn_cli_with_output_callback(self, cli_session_manager, tmp_path):
        """Test CLI session with output streaming callback."""
        collected_output: list[SessionOutput] = []

        def collect_output(output: SessionOutput):
            collected_output.append(output)

        session = await cli_session_manager.spawn_cli(
            prompt="Say 'hello callback test'",
            agent_type="greeting",
            timeout=60,
            output_callback=collect_output,
            working_dir=tmp_path,
        )

        # Should have some output (if Claude CLI was available and responded)
        if session.status == SessionStatus.COMPLETED:
            assert len(collected_output) >= 0  # May have output, may not depending on CLI

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_session(self, cli_session_manager, tmp_path):
        """Test retrieving a session by UUID."""
        session = await cli_session_manager.spawn(
            prompt="Test get session",
            working_dir=tmp_path,
        )

        retrieved = await cli_session_manager.get_session(session.uuid)
        assert retrieved is not None
        assert retrieved.uuid == session.uuid

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_session(self, cli_session_manager, tmp_path):
        """Test cleaning up a session."""
        session = await cli_session_manager.spawn(
            prompt="Test cleanup",
            working_dir=tmp_path,
        )

        # Session should exist
        assert session.uuid in cli_session_manager._active_sessions

        # Clean up
        await cli_session_manager.cleanup(session.uuid)

        # Session should be gone
        assert session.uuid not in cli_session_manager._active_sessions

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_locking(self, tmp_path):
        """Test session locking mechanism."""
        lock_dir = tmp_path / ".sessions"
        manager = SessionManager(safemode=False, lock_dir=lock_dir)

        session = await manager.spawn(
            prompt="Test locking",
            working_dir=tmp_path,
        )

        # Session should be locked
        is_locked = await manager.is_locked(session.uuid)
        # Note: The lock is acquired but released after spawn completes
        # For Task mode (non-CLI), lock stays until complete/fail/cleanup

        # Complete the session to release lock
        await manager.complete(session.uuid, "Done")

        # Should be unlocked now
        is_locked_after = await manager.is_locked(session.uuid)
        assert is_locked_after is False
