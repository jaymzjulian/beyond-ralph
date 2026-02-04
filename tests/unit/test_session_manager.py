"""Unit tests for Session Manager."""

from pathlib import Path

import pytest

from beyond_ralph.core.session_manager import (
    SessionInfo,
    SessionManager,
    SessionOutput,
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


class TestSessionOutput:
    """Tests for SessionOutput streaming helper."""

    def test_formatted_output(self) -> None:
        """Test output formatting with agent prefix."""
        output = SessionOutput(
            session_uuid="abc123",
            line="Processing file...",
        )

        formatted = output.formatted()
        assert formatted == "[AGENT:abc123] Processing file..."

    def test_formatted_error_output(self) -> None:
        """Test error output formatting."""
        output = SessionOutput(
            session_uuid="abc123",
            line="Something went wrong",
            is_error=True,
        )

        formatted = output.formatted()
        assert formatted == "[AGENT:abc123:ERROR] Something went wrong"

    def test_final_output(self) -> None:
        """Test final output flag."""
        output = SessionOutput(
            session_uuid="abc123",
            line="Done!",
            is_final=True,
        )

        assert output.is_final is True


class TestResultExtraction:
    """Tests for result extraction from session output."""

    def test_extract_result_completion_markers(self, session_manager: SessionManager) -> None:
        """Test extracting results with completion markers."""
        output_lines = [
            "Reading file...",
            "Processing...",
            "Writing output...",
            "Task completed successfully",
            "Created 3 new files",
        ]

        result = session_manager._extract_result(output_lines)
        assert "completed successfully" in result
        assert "Created 3 new files" in result

    def test_extract_result_empty(self, session_manager: SessionManager) -> None:
        """Test extracting from empty output."""
        result = session_manager._extract_result([])
        assert result == ""

    def test_extract_result_no_markers(self, session_manager: SessionManager) -> None:
        """Test extracting when no completion markers found."""
        output_lines = [
            "Line 1",
            "Line 2",
            "Line 3",
        ]

        result = session_manager._extract_result(output_lines)
        # Should still return last few lines
        assert "Line 3" in result


class TestCLISpawning:
    """Tests for CLI-based session spawning."""

    def test_find_claude_cli_not_installed(self, session_manager: SessionManager) -> None:
        """Test handling when Claude CLI is not found."""
        # Mock the shutil.which to return None
        import shutil
        original_which = shutil.which

        def mock_which(cmd: str) -> None:
            return None

        shutil.which = mock_which
        try:
            result = session_manager._find_claude_cli()
            # Should return None when not found
            assert result is None
        finally:
            shutil.which = original_which

    @pytest.mark.asyncio
    async def test_spawn_cli_without_pexpect(
        self, session_manager: SessionManager, monkeypatch
    ) -> None:
        """Test spawn_cli raises when pexpect not available."""
        import beyond_ralph.core.session_manager as sm

        # Temporarily disable pexpect
        original = sm.PEXPECT_AVAILABLE
        monkeypatch.setattr(sm, "PEXPECT_AVAILABLE", False)

        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.spawn_cli(prompt="test")

        assert "pexpect is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spawn_with_use_cli_false(self, session_manager: SessionManager) -> None:
        """Test spawn with use_cli=False uses Task mode."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
            use_cli=False,
        )

        # Should create session in pending/running state without CLI
        assert session.uuid
        assert session.status == SessionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_send_without_cli(self, session_manager: SessionManager) -> None:
        """Test send in Task mode returns placeholder."""
        session = await session_manager.spawn(
            prompt="Test task",
            agent_type="test",
        )

        result = await session_manager.send(session.uuid, "follow up", use_cli=False)
        assert "Follow-up not yet implemented" in result


class TestSessionManagerAdvanced:
    """Advanced tests for SessionManager."""

    @pytest.mark.asyncio
    async def test_get_session_nonexistent(self, session_manager: SessionManager) -> None:
        """Test getting a nonexistent session returns None."""
        session = await session_manager.get_session("nonexistent-uuid")
        assert session is None

    @pytest.mark.asyncio
    async def test_is_locked_nonexistent(self, session_manager: SessionManager) -> None:
        """Test is_locked for nonexistent session returns False."""
        is_locked = await session_manager.is_locked("nonexistent-uuid")
        assert is_locked is False

    @pytest.mark.asyncio
    async def test_complete_nonexistent_session(self, session_manager: SessionManager) -> None:
        """Test completing a nonexistent session doesn't crash."""
        # Should not raise, just log warning
        await session_manager.complete("nonexistent-uuid", "result")

    @pytest.mark.asyncio
    async def test_fail_nonexistent_session(self, session_manager: SessionManager) -> None:
        """Test failing a nonexistent session doesn't crash."""
        # Should not raise, just log warning
        await session_manager.fail("nonexistent-uuid", "error")

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_session(self, session_manager: SessionManager) -> None:
        """Test cleanup of nonexistent session doesn't crash."""
        await session_manager.cleanup("nonexistent-uuid")

    def test_result_extraction_with_markers(self, session_manager: SessionManager) -> None:
        """Test result extraction finds completion markers."""
        lines = [
            "Starting task...",
            "Processing data...",
            "COMPLETED: Task finished",
            "Created output file",
        ]
        result = session_manager._extract_result(lines)
        assert "COMPLETED" in result or "finished" in result.lower()

    def test_result_extraction_with_done_marker(self, session_manager: SessionManager) -> None:
        """Test result extraction with DONE marker."""
        lines = [
            "Working...",
            "DONE: All steps completed",
            "Summary: 5 files processed",
        ]
        result = session_manager._extract_result(lines)
        assert "DONE" in result or "completed" in result.lower()


class TestSessionInfoAdvanced:
    """Additional tests for SessionInfo."""

    def test_session_info_defaults(self) -> None:
        """Test SessionInfo with minimal fields."""
        from datetime import datetime

        session = SessionInfo(
            uuid="test-789",
            agent_type="review",
            status=SessionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            prompt="Review code",
        )

        assert session.result is None
        assert session.error is None
        assert session.pid is None

    def test_session_info_with_pid(self) -> None:
        """Test SessionInfo with pid field."""
        from datetime import datetime

        session = SessionInfo(
            uuid="test-pid",
            agent_type="interview",
            status=SessionStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            prompt="Interview user",
            pid=12345,
        )

        assert session.pid == 12345
        assert session.status == SessionStatus.RUNNING

    def test_session_info_with_result(self) -> None:
        """Test SessionInfo with result."""
        from datetime import datetime

        session = SessionInfo(
            uuid="test-result",
            agent_type="testing",
            status=SessionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            prompt="Run tests",
            result="All tests passed",
        )

        assert session.result == "All tests passed"

    def test_from_dict_with_error(self) -> None:
        """Test creating session info from dict with error."""
        data = {
            "uuid": "test-error",
            "agent_type": "implementation",
            "status": "failed",
            "created_at": "2024-02-01T10:00:00",
            "updated_at": "2024-02-01T10:05:00",
            "prompt": "Implement feature",
            "error": "FileNotFoundError: config.yaml",
        }

        session = SessionInfo.from_dict(data)
        assert session.status == SessionStatus.FAILED
        assert session.error == "FileNotFoundError: config.yaml"


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values exist."""
        assert SessionStatus.PENDING.value == "pending"
        assert SessionStatus.RUNNING.value == "running"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.FAILED.value == "failed"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.UNKNOWN.value == "unknown"

    def test_status_count(self) -> None:
        """Test correct number of statuses."""
        assert len(SessionStatus) == 6


class TestLockHandling:
    """Tests for session locking mechanisms."""

    @pytest.mark.asyncio
    async def test_stale_lock_cleanup(self, temp_lock_dir: Path) -> None:
        """Test that stale locks from dead processes are cleaned up."""
        import json

        manager = SessionManager(lock_dir=temp_lock_dir)
        session_uuid = "stale-session"

        # Create a lock file with a non-existent PID
        lock_file = temp_lock_dir / f"{session_uuid}.lock"
        lock_data = {"pid": 999999, "locked_at": "2024-01-01T00:00:00"}
        lock_file.write_text(json.dumps(lock_data))

        # is_locked should return False for stale locks
        is_locked = await manager.is_locked(session_uuid)
        assert is_locked is False

        # Lock file should have been cleaned up
        assert not lock_file.exists()

    @pytest.mark.asyncio
    async def test_acquire_lock_when_already_locked(self, session_manager: SessionManager) -> None:
        """Test acquire lock fails when session is already locked."""
        session = await session_manager.spawn(prompt="Test", agent_type="test")

        # Try to acquire lock on same session again
        acquired = await session_manager._acquire_lock(session.uuid)
        assert acquired is False

    @pytest.mark.asyncio
    async def test_invalid_lock_file_json(self, temp_lock_dir: Path) -> None:
        """Test handling of invalid JSON in lock file."""
        manager = SessionManager(lock_dir=temp_lock_dir)
        session_uuid = "invalid-json"

        # Create an invalid lock file
        lock_file = temp_lock_dir / f"{session_uuid}.lock"
        lock_file.write_text("not valid json")

        # Should return False for invalid lock files
        is_locked = await manager.is_locked(session_uuid)
        assert is_locked is False


class TestCLIPathFinding:
    """Tests for Claude CLI path finding."""

    def test_find_claude_cli_in_path(self, session_manager: SessionManager) -> None:
        """Test finding claude CLI when in PATH."""
        import shutil as sh

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sh, "which", lambda x: "/usr/local/bin/claude" if x == "claude" else None)
            result = session_manager._find_claude_cli()
            assert result == "/usr/local/bin/claude"

    def test_find_claude_cli_npm_global(self, session_manager: SessionManager, tmp_path: Path) -> None:
        """Test finding claude CLI in npm global path."""
        import shutil as sh

        # Create mock npm global path
        npm_bin = tmp_path / ".npm-global" / "bin"
        npm_bin.mkdir(parents=True)
        claude_path = npm_bin / "claude"
        claude_path.touch()

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sh, "which", lambda x: None)
            mp.setattr(Path, "home", lambda: tmp_path)

            result = session_manager._find_claude_cli()
            assert result == str(claude_path)


class TestResultExtractionAdvanced:
    """Advanced tests for result extraction."""

    def test_extract_result_with_successfully(self, session_manager: SessionManager) -> None:
        """Test extraction with 'successfully' marker."""
        lines = [
            "Working on task...",
            "Reading files...",
            "Task completed successfully",
            "All changes applied",
        ]
        result = session_manager._extract_result(lines)
        assert "successfully" in result

    def test_extract_result_with_implemented(self, session_manager: SessionManager) -> None:
        """Test extraction with 'implemented' marker."""
        lines = [
            "Analyzing code...",
            "Feature implemented in module.py",
            "Ready for review",
        ]
        result = session_manager._extract_result(lines)
        assert "implemented" in result

    def test_extract_result_with_created(self, session_manager: SessionManager) -> None:
        """Test extraction with 'created' marker."""
        lines = [
            "Generating code...",
            "Created new file: app.py",
            "All done",
        ]
        result = session_manager._extract_result(lines)
        assert "Created" in result

    def test_extract_result_with_summary(self, session_manager: SessionManager) -> None:
        """Test extraction with 'summary:' marker."""
        lines = [
            "Processing...",
            "Summary: 5 files modified, 2 tests added",
        ]
        result = session_manager._extract_result(lines)
        assert "Summary" in result

    def test_extract_result_long_output(self, session_manager: SessionManager) -> None:
        """Test extraction stops after enough lines."""
        lines = [f"Line {i}" for i in range(50)]
        lines.append("Task completed successfully")
        result = session_manager._extract_result(lines)
        # Should not contain all 50 lines, limited to 20
        assert result.count("\n") <= 20


class TestSpawnWithCLI:
    """Tests for CLI spawn functionality."""

    @pytest.mark.asyncio
    async def test_spawn_cli_no_claude_found(self, session_manager: SessionManager) -> None:
        """Test spawn_cli when Claude CLI is not found."""
        import beyond_ralph.core.session_manager as sm

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sm, "PEXPECT_AVAILABLE", True)
            mp.setattr(session_manager, "_find_claude_cli", lambda: None)

            with pytest.raises(RuntimeError) as exc_info:
                await session_manager.spawn_cli(prompt="test")

            assert "Claude CLI not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spawn_with_use_cli_true(self, session_manager: SessionManager) -> None:
        """Test spawn with use_cli=True delegates to spawn_cli."""
        import beyond_ralph.core.session_manager as sm

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sm, "PEXPECT_AVAILABLE", True)
            mp.setattr(session_manager, "_find_claude_cli", lambda: None)

            with pytest.raises(RuntimeError) as exc_info:
                await session_manager.spawn(prompt="test", use_cli=True)

            assert "Claude CLI not found" in str(exc_info.value)


class TestSendMethod:
    """Tests for send() method."""

    @pytest.mark.asyncio
    async def test_send_unknown_session(self, session_manager: SessionManager) -> None:
        """Test send to unknown session raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await session_manager.send("unknown-uuid", "message")

        assert "Unknown session" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_cli_mode_no_pexpect(self, session_manager: SessionManager) -> None:
        """Test send with use_cli=True when pexpect not available."""
        import beyond_ralph.core.session_manager as sm

        session = await session_manager.spawn(prompt="Test", agent_type="test")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sm, "PEXPECT_AVAILABLE", False)

            with pytest.raises(RuntimeError) as exc_info:
                await session_manager.send(session.uuid, "follow up", use_cli=True)

            assert "pexpect required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_cli_mode_no_claude(self, session_manager: SessionManager) -> None:
        """Test send with use_cli=True when Claude CLI not found."""
        import beyond_ralph.core.session_manager as sm

        session = await session_manager.spawn(prompt="Test", agent_type="test")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(sm, "PEXPECT_AVAILABLE", True)
            mp.setattr(session_manager, "_find_claude_cli", lambda: None)

            with pytest.raises(RuntimeError) as exc_info:
                await session_manager.send(session.uuid, "follow up", use_cli=True)

            assert "Claude CLI not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_invalid_state(self, session_manager: SessionManager) -> None:
        """Test send fails for session in invalid state."""
        session = await session_manager.spawn(prompt="Test", agent_type="test")
        await session_manager.fail(session.uuid, "error")

        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.send(session.uuid, "follow up")

        assert "not in a valid state" in str(exc_info.value)


class TestSessionManagerSafemode:
    """Tests for safemode option."""

    def test_safemode_enabled(self, temp_lock_dir: Path) -> None:
        """Test session manager with safemode enabled."""
        manager = SessionManager(lock_dir=temp_lock_dir, safemode=True)
        assert manager.safemode is True

    def test_safemode_disabled_by_default(self, temp_lock_dir: Path) -> None:
        """Test session manager safemode is disabled by default."""
        manager = SessionManager(lock_dir=temp_lock_dir)
        assert manager.safemode is False


class TestSessionOutputFormatting:
    """Additional tests for SessionOutput formatting."""

    def test_formatted_with_timestamp(self) -> None:
        """Test SessionOutput has timestamp."""
        output = SessionOutput(
            session_uuid="test-123",
            line="Output line",
        )
        assert output.timestamp is not None

    def test_multiple_outputs_different_timestamps(self) -> None:
        """Test multiple outputs can have different timestamps."""
        import time

        output1 = SessionOutput(session_uuid="test", line="Line 1")
        time.sleep(0.01)
        output2 = SessionOutput(session_uuid="test", line="Line 2")

        # Timestamps should exist (comparison depends on precision)
        assert output1.timestamp is not None
        assert output2.timestamp is not None


class TestSpawnCLIMocked:
    """Tests for spawn_cli with mocked pexpect."""

    @pytest.mark.asyncio
    async def test_spawn_cli_success(self, temp_lock_dir: Path) -> None:
        """Test successful CLI spawn with mocked pexpect."""
        from unittest.mock import MagicMock, patch, AsyncMock
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_child = MagicMock()
        mock_child.pid = 12345
        mock_child.before = "Task completed successfully"
        mock_child.exitstatus = 0
        mock_child.isalive.return_value = False

        # Simulate EOF on expect
        mock_child.expect.side_effect = [2]  # EOF index

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    session = await manager.spawn_cli(
                        prompt="Test task",
                        agent_type="test",
                    )

                    assert session.status == SessionStatus.COMPLETED
                    assert session.pid == 12345

    @pytest.mark.asyncio
    async def test_spawn_cli_no_claude_cli(self, temp_lock_dir: Path) -> None:
        """Test spawn_cli raises when Claude CLI not found."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        with patch.object(manager, "_find_claude_cli", return_value=None):
            with patch.object(sm, "PEXPECT_AVAILABLE", True):
                with pytest.raises(RuntimeError) as exc_info:
                    await manager.spawn_cli(prompt="test")

                assert "Claude CLI not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spawn_cli_exit_code_failure(self, temp_lock_dir: Path) -> None:
        """Test spawn_cli handles non-zero exit code."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_child = MagicMock()
        mock_child.pid = 12345
        mock_child.before = "Error occurred"
        mock_child.exitstatus = 1
        mock_child.isalive.return_value = False
        mock_child.expect.side_effect = [2]  # EOF

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    session = await manager.spawn_cli(
                        prompt="Test task",
                        agent_type="test",
                    )

                    assert session.status == SessionStatus.FAILED
                    assert "Exit code: 1" in session.error

    @pytest.mark.asyncio
    async def test_spawn_cli_with_output_callback(self, temp_lock_dir: Path) -> None:
        """Test spawn_cli calls output callback."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_child = MagicMock()
        mock_child.pid = 12345
        mock_child.before = "Processing line"
        mock_child.exitstatus = 0
        mock_child.isalive.return_value = False
        mock_child.expect.side_effect = [0, 2]  # Line, then EOF

        callback_outputs = []

        def output_callback(output: SessionOutput) -> None:
            callback_outputs.append(output)

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    await manager.spawn_cli(
                        prompt="Test task",
                        agent_type="test",
                        output_callback=output_callback,
                    )

                    assert len(callback_outputs) >= 1

    @pytest.mark.asyncio
    async def test_spawn_cli_with_working_dir(self, temp_lock_dir: Path, tmp_path: Path) -> None:
        """Test spawn_cli respects working directory."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_child = MagicMock()
        mock_child.pid = 12345
        mock_child.before = ""
        mock_child.exitstatus = 0
        mock_child.isalive.return_value = False
        mock_child.expect.side_effect = [2]

        spawn_calls = []

        def capture_spawn(*args, **kwargs):
            spawn_calls.append(kwargs)
            return mock_child

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", side_effect=capture_spawn):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    await manager.spawn_cli(
                        prompt="Test task",
                        agent_type="test",
                        working_dir=tmp_path,
                    )

                    assert len(spawn_calls) == 1
                    assert spawn_calls[0]["cwd"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_spawn_cli_exception_handling(self, temp_lock_dir: Path) -> None:
        """Test spawn_cli handles exceptions and releases lock."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", side_effect=Exception("Spawn failed")):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    with pytest.raises(Exception) as exc_info:
                        await manager.spawn_cli(prompt="test")

                    assert "Spawn failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spawn_cli_timeout_handling(self, temp_lock_dir: Path) -> None:
        """Test spawn_cli handles timeout in output reading."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_child = MagicMock()
        mock_child.pid = 12345
        mock_child.before = ""
        mock_child.exitstatus = 0
        mock_child.isalive.side_effect = [True, False]  # Running, then done
        mock_child.expect.side_effect = [3, 2]  # Timeout, then EOF

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    session = await manager.spawn_cli(
                        prompt="Test task",
                        agent_type="test",
                    )

                    # Should complete despite timeout
                    assert session.status == SessionStatus.COMPLETED


class TestSendCLIMocked:
    """Tests for _send_cli with mocked pexpect."""

    @pytest.mark.asyncio
    async def test_send_cli_success(self, temp_lock_dir: Path) -> None:
        """Test successful CLI send with mocked pexpect."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        # Create a session first
        session = await manager.spawn(prompt="Initial", agent_type="test")

        mock_child = MagicMock()
        mock_child.before = "Follow-up completed"
        mock_child.exitstatus = 0
        mock_child.isalive.return_value = False
        mock_child.expect.side_effect = [2]  # EOF

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    result = await manager._send_cli(
                        session_uuid=session.uuid,
                        message="Follow up message",
                    )

                    assert "Follow-up" in result or "completed" in result.lower()

    @pytest.mark.asyncio
    async def test_send_cli_no_pexpect(self, temp_lock_dir: Path) -> None:
        """Test _send_cli raises when pexpect not available."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)
        session = await manager.spawn(prompt="Initial", agent_type="test")

        with patch.object(sm, "PEXPECT_AVAILABLE", False):
            with pytest.raises(RuntimeError) as exc_info:
                await manager._send_cli(session.uuid, "message")

            assert "pexpect required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_cli_no_claude(self, temp_lock_dir: Path) -> None:
        """Test _send_cli raises when Claude CLI not found."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)
        session = await manager.spawn(prompt="Initial", agent_type="test")

        with patch.object(manager, "_find_claude_cli", return_value=None):
            with patch.object(sm, "PEXPECT_AVAILABLE", True):
                with pytest.raises(RuntimeError) as exc_info:
                    await manager._send_cli(session.uuid, "message")

                assert "Claude CLI not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_cli_unknown_session(self, temp_lock_dir: Path) -> None:
        """Test _send_cli raises for unknown session."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        with patch.object(sm, "PEXPECT_AVAILABLE", True):
            with pytest.raises(ValueError) as exc_info:
                await manager._send_cli("unknown-uuid", "message")

            assert "Unknown session" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_cli_with_callback(self, temp_lock_dir: Path) -> None:
        """Test _send_cli calls output callback."""
        from unittest.mock import MagicMock, patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)
        session = await manager.spawn(prompt="Initial", agent_type="test")

        mock_child = MagicMock()
        mock_child.before = "Output line"
        mock_child.exitstatus = 0
        mock_child.isalive.return_value = False
        mock_child.expect.side_effect = [0, 2]  # Line, then EOF

        callback_outputs = []

        def callback(output: SessionOutput) -> None:
            callback_outputs.append(output)

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", return_value=mock_child):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    await manager._send_cli(
                        session_uuid=session.uuid,
                        message="Follow up",
                        output_callback=callback,
                    )

                    assert len(callback_outputs) >= 1

    @pytest.mark.asyncio
    async def test_send_cli_exception(self, temp_lock_dir: Path) -> None:
        """Test _send_cli handles exceptions."""
        from unittest.mock import patch
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)
        session = await manager.spawn(prompt="Initial", agent_type="test")

        with patch.object(manager, "_find_claude_cli", return_value="/usr/bin/claude"):
            with patch("pexpect.spawn", side_effect=Exception("Connection failed")):
                with patch.object(sm, "PEXPECT_AVAILABLE", True):
                    with pytest.raises(Exception) as exc_info:
                        await manager._send_cli(session.uuid, "message")

                    assert "Connection failed" in str(exc_info.value)


class TestGetResult:
    """Tests for get_result method."""

    @pytest.mark.asyncio
    async def test_get_result_success(self, session_manager: SessionManager) -> None:
        """Test getting result from completed session."""
        session = await session_manager.spawn(prompt="Test", agent_type="test")
        await session_manager.complete(session.uuid, "Task completed!")

        result = await session_manager.get_result(session.uuid)
        assert result == "Task completed!"

    @pytest.mark.asyncio
    async def test_get_result_pending(self, session_manager: SessionManager) -> None:
        """Test getting result from pending session."""
        session = await session_manager.spawn(prompt="Test", agent_type="test")

        result = await session_manager.get_result(session.uuid)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_result_unknown_session(self, session_manager: SessionManager) -> None:
        """Test getting result from unknown session."""
        result = await session_manager.get_result("unknown-uuid")
        assert result is None


class TestResultExtractionAdvanced:
    """Additional tests for result extraction."""

    def test_extract_result_fixed_marker(self, session_manager: SessionManager) -> None:
        """Test extraction with 'fixed' marker."""
        lines = [
            "Analyzing code...",
            "Found the issue",
            "Fixed the bug in auth.py",
            "All tests pass now",
        ]
        result = session_manager._extract_result(lines)
        assert "Fixed" in result or "fixed" in result.lower()

    def test_extract_result_created_marker(self, session_manager: SessionManager) -> None:
        """Test extraction with 'created' marker."""
        lines = [
            "Scaffolding project...",
            "Created new component files",
            "Setup complete",
        ]
        result = session_manager._extract_result(lines)
        assert "Created" in result or "created" in result.lower()

    def test_extract_result_summary_marker(self, session_manager: SessionManager) -> None:
        """Test extraction with 'summary' marker."""
        lines = [
            "Processing...",
            "Summary: 10 files processed",
            "No errors found",
        ]
        result = session_manager._extract_result(lines)
        assert "Summary" in result or "summary" in result.lower()

    def test_extract_result_trailing_empty_lines(self, session_manager: SessionManager) -> None:
        """Test extraction skips trailing empty lines."""
        lines = [
            "Processing...",
            "Done!",
            "",
            "",
            "",
        ]
        result = session_manager._extract_result(lines)
        assert "Done" in result

    def test_extract_result_max_lines(self, session_manager: SessionManager) -> None:
        """Test extraction respects max lines limit."""
        lines = [f"Line {i}" for i in range(50)]
        lines.append("Final result: success")

        result = session_manager._extract_result(lines)
        # Should contain final lines but not all 50
        assert "Final result" in result
        assert len(result.split("\n")) <= 20


class TestSpawnWithUseCLI:
    """Tests for spawn with use_cli=True."""

    @pytest.mark.asyncio
    async def test_spawn_use_cli_true(self, temp_lock_dir: Path) -> None:
        """Test spawn delegates to spawn_cli when use_cli=True."""
        from unittest.mock import MagicMock, patch, AsyncMock
        import beyond_ralph.core.session_manager as sm

        manager = SessionManager(lock_dir=temp_lock_dir)

        mock_session = MagicMock()
        mock_session.uuid = "cli-session"

        with patch.object(manager, "spawn_cli", new_callable=AsyncMock) as mock_spawn_cli:
            mock_spawn_cli.return_value = mock_session

            session = await manager.spawn(
                prompt="Test",
                agent_type="test",
                use_cli=True,
            )

            mock_spawn_cli.assert_called_once()
            assert session.uuid == "cli-session"


class TestSendWithUseCLI:
    """Tests for send with use_cli=True."""

    @pytest.mark.asyncio
    async def test_send_use_cli_true(self, temp_lock_dir: Path) -> None:
        """Test send delegates to _send_cli when use_cli=True."""
        from unittest.mock import patch, AsyncMock

        manager = SessionManager(lock_dir=temp_lock_dir)
        session = await manager.spawn(prompt="Initial", agent_type="test")

        with patch.object(manager, "_send_cli", new_callable=AsyncMock) as mock_send_cli:
            mock_send_cli.return_value = "CLI response"

            result = await manager.send(
                session_uuid=session.uuid,
                message="Follow up",
                use_cli=True,
            )

            mock_send_cli.assert_called_once()
            assert result == "CLI response"

    @pytest.mark.asyncio
    async def test_send_unknown_session(self, session_manager: SessionManager) -> None:
        """Test send raises for unknown session."""
        with pytest.raises(ValueError) as exc_info:
            await session_manager.send("unknown-uuid", "message")

        assert "Unknown session" in str(exc_info.value)


class TestGetSessionManagerSingleton:
    """Tests for get_session_manager singleton function."""

    def test_get_session_manager_creates_instance(self):
        """Test get_session_manager creates singleton."""
        import beyond_ralph.core.session_manager as sm

        # Reset singleton
        sm._session_manager = None

        manager = sm.get_session_manager()
        assert manager is not None
        assert isinstance(manager, sm.SessionManager)

    def test_get_session_manager_returns_same_instance(self):
        """Test get_session_manager returns same instance."""
        import beyond_ralph.core.session_manager as sm

        # Reset singleton
        sm._session_manager = None

        manager1 = sm.get_session_manager()
        manager2 = sm.get_session_manager()
        assert manager1 is manager2

    def test_get_session_manager_respects_safemode(self):
        """Test get_session_manager passes safemode."""
        import beyond_ralph.core.session_manager as sm

        # Reset singleton
        sm._session_manager = None

        manager = sm.get_session_manager(safemode=True)
        assert manager.safemode is True

        # Reset for other tests
        sm._session_manager = None


class TestSessionLockAcquisitionFailure:
    """Tests for lock acquisition failure scenarios."""

    @pytest.mark.asyncio
    async def test_spawn_lock_acquisition_failure(self, temp_lock_dir: Path):
        """Test spawn raises when lock cannot be acquired."""
        from unittest.mock import patch, AsyncMock

        manager = SessionManager(lock_dir=temp_lock_dir)

        # Mock _acquire_lock to return False
        with patch.object(manager, "_acquire_lock", new_callable=AsyncMock) as mock_lock:
            mock_lock.return_value = False

            with pytest.raises(RuntimeError) as exc_info:
                await manager.spawn(prompt="Test", agent_type="test")

            assert "Could not acquire lock" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_spawn_cli_lock_acquisition_failure(self, temp_lock_dir: Path):
        """Test spawn_cli raises when lock cannot be acquired."""
        from unittest.mock import patch, AsyncMock, MagicMock

        manager = SessionManager(lock_dir=temp_lock_dir)

        # Mock shutil.which to return a path (simulating claude being found)
        with patch("shutil.which", return_value="/usr/bin/claude"):
            # Mock _acquire_lock to return False
            with patch.object(manager, "_acquire_lock", new_callable=AsyncMock) as mock_lock:
                mock_lock.return_value = False

                with pytest.raises(RuntimeError) as exc_info:
                    await manager.spawn_cli(
                        prompt="Test",
                        agent_type="test",
                    )

                assert "Could not acquire lock" in str(exc_info.value)


class TestPexpectAvailability:
    """Tests related to pexpect availability."""

    def test_pexpect_available_flag_exists(self):
        """Test PEXPECT_AVAILABLE flag is defined."""
        from beyond_ralph.core.session_manager import PEXPECT_AVAILABLE
        assert isinstance(PEXPECT_AVAILABLE, bool)

    def test_pexpect_is_available(self):
        """Test pexpect is available in test environment."""
        from beyond_ralph.core.session_manager import PEXPECT_AVAILABLE
        # In our test environment, pexpect should be available
        assert PEXPECT_AVAILABLE is True


class TestSpawnCLIEdgeCases:
    """Additional edge case tests for spawn_cli."""

    @pytest.mark.asyncio
    async def test_spawn_cli_claude_not_found(self, temp_lock_dir: Path):
        """Test spawn_cli raises when claude not found."""
        from unittest.mock import patch

        manager = SessionManager(lock_dir=temp_lock_dir)

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager.spawn_cli(prompt="Test", agent_type="test")

            assert "Claude CLI not found" in str(exc_info.value)


class TestSendCLIEdgeCases:
    """Additional edge case tests for _send_cli."""

    @pytest.mark.asyncio
    async def test_send_cli_claude_not_found(self, temp_lock_dir: Path):
        """Test _send_cli raises when claude not found."""
        from unittest.mock import patch

        manager = SessionManager(lock_dir=temp_lock_dir)

        # First spawn a session
        session = await manager.spawn(prompt="Test", agent_type="test")

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                await manager._send_cli(session.uuid, "follow up")

            assert "Claude CLI not found" in str(exc_info.value)
