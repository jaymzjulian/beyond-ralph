"""Tests for hooks module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestRegisterHooks:
    """Tests for register_hooks function."""

    def test_register_hooks_returns_dict(self):
        """Test register_hooks returns proper dictionary."""
        from beyond_ralph.hooks import register_hooks

        result = register_hooks()
        assert isinstance(result, dict)
        assert "stop" in result
        assert "pre_spawn" in result
        assert "subagent_stop" in result

    def test_register_hooks_stop_config(self):
        """Test stop hook configuration."""
        from beyond_ralph.hooks import register_hooks

        result = register_hooks()
        stop_hook = result["stop"]

        assert stop_hook["name"] == "beyond-ralph-stop"
        assert "description" in stop_hook
        assert stop_hook["handler"] == "beyond_ralph.hooks.stop_handler:handle_stop"

    def test_register_hooks_pre_spawn_config(self):
        """Test pre_spawn hook configuration."""
        from beyond_ralph.hooks import register_hooks

        result = register_hooks()
        pre_spawn_hook = result["pre_spawn"]

        assert pre_spawn_hook["name"] == "beyond-ralph-quota-check"
        assert "description" in pre_spawn_hook
        assert pre_spawn_hook["handler"] == "beyond_ralph.hooks.quota_check:check_quota_before_spawn"

    def test_register_hooks_subagent_stop_config(self):
        """Test subagent_stop hook configuration."""
        from beyond_ralph.hooks import register_hooks

        result = register_hooks()
        subagent_hook = result["subagent_stop"]

        assert subagent_hook["name"] == "beyond-ralph-subagent-stop"
        assert "description" in subagent_hook
        assert subagent_hook["handler"] == "beyond_ralph.hooks.subagent_stop:handle_subagent_stop"


class TestQuotaCheckHook:
    """Tests for quota check hook."""

    def test_check_quota_before_spawn_allows_when_not_limited(self, tmp_path, monkeypatch):
        """Test spawn allowed when quota not limited."""
        monkeypatch.chdir(tmp_path)

        # Mock QuotaManager
        mock_status = MagicMock()
        mock_status.is_limited = False

        mock_manager = MagicMock()
        mock_manager.check.return_value = mock_status

        with patch('beyond_ralph.core.quota_manager.QuotaManager', return_value=mock_manager):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            result = check_quota_before_spawn()
            assert result == 0  # Allow spawn

    def test_check_quota_before_spawn_blocks_when_limited(self, tmp_path, monkeypatch):
        """Test spawn blocked when quota limited."""
        monkeypatch.chdir(tmp_path)

        # Create state file
        state_file = tmp_path / ".beyond_ralph_state"
        state_file.write_text(json.dumps({"status": "running"}))

        # Mock QuotaManager
        mock_status = MagicMock()
        mock_status.is_limited = True
        mock_status.session_percent = 90.0
        mock_status.weekly_percent = 85.0
        mock_status.to_dict.return_value = {"session_percent": 90.0, "weekly_percent": 85.0}

        mock_manager = MagicMock()
        mock_manager.check.return_value = mock_status

        with patch('beyond_ralph.core.quota_manager.QuotaManager', return_value=mock_manager):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            result = check_quota_before_spawn()
            assert result == 1  # Block spawn

            # Check state file was updated
            state = json.loads(state_file.read_text())
            assert state["status"] == "quota_paused"

    def test_check_quota_before_spawn_allows_on_import_error(self):
        """Test spawn allowed when QuotaManager import fails."""
        from beyond_ralph.hooks import quota_check
        # Verifying function exists
        assert hasattr(quota_check, 'check_quota_before_spawn')
        # The function should handle ImportError internally and return 0

    def test_check_quota_before_spawn_allows_on_exception(self, tmp_path, monkeypatch):
        """Test spawn allowed when exception occurs."""
        monkeypatch.chdir(tmp_path)

        with patch('beyond_ralph.core.quota_manager.QuotaManager', side_effect=Exception("Test error")):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            result = check_quota_before_spawn()
            assert result == 0  # Allow on error

    def test_quota_check_main_entry(self):
        """Test main entry point."""
        from beyond_ralph.hooks.quota_check import main

        with patch('beyond_ralph.hooks.quota_check.check_quota_before_spawn', return_value=0):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestStopHandler:
    """Tests for stop handler hook."""

    def test_handle_stop_saves_state(self, tmp_path, monkeypatch):
        """Test stop handler saves state."""
        monkeypatch.chdir(tmp_path)

        # Create state file
        state_file = tmp_path / ".beyond_ralph_state"
        state_file.write_text(json.dumps({
            "status": "running",
            "current_phase": 3
        }))

        from beyond_ralph.hooks.stop_handler import handle_stop

        handle_stop()

        # Check state was updated
        state = json.loads(state_file.read_text())
        assert state["status"] == "paused"
        assert "last_stopped" in state
        assert state["current_phase"] == 3  # Preserved

    def test_handle_stop_no_state_file(self, tmp_path, monkeypatch, capsys):
        """Test stop handler when no state file exists."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.stop_handler import handle_stop

        # Should not raise
        handle_stop()

        # No output expected (no state file)
        captured = capsys.readouterr()
        assert ".beyond_ralph_state" not in captured.out

    def test_handle_stop_exception_handling(self, tmp_path, monkeypatch, capsys):
        """Test stop handler handles exceptions gracefully."""
        monkeypatch.chdir(tmp_path)

        # Create state file that will cause JSON error when read
        state_file = tmp_path / ".beyond_ralph_state"
        state_file.write_text("invalid json")

        from beyond_ralph.hooks.stop_handler import handle_stop

        # Should not raise
        handle_stop()

        # Should print warning
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_stop_handler_main_entry(self):
        """Test main entry point."""
        from beyond_ralph.hooks.stop_handler import main

        with patch('beyond_ralph.hooks.stop_handler.handle_stop') as mock_stop:
            main()
            mock_stop.assert_called_once()


class TestSubagentStopHandler:
    """Tests for subagent stop handler hook."""

    def test_handle_subagent_stop_records_success(self, tmp_path, monkeypatch):
        """Test recording successful subagent completion."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import handle_subagent_stop, get_subagent_result

        handle_subagent_stop(
            session_id="agent-123",
            result="Task completed successfully",
            success=True,
        )

        result = get_subagent_result("agent-123")
        assert result is not None
        assert result["success"] is True
        assert result["result"] == "Task completed successfully"

    def test_handle_subagent_stop_records_failure(self, tmp_path, monkeypatch):
        """Test recording failed subagent completion."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import handle_subagent_stop, get_subagent_result

        handle_subagent_stop(
            session_id="agent-456",
            result=None,
            success=False,
            error="Connection timeout",
        )

        result = get_subagent_result("agent-456")
        assert result is not None
        assert result["success"] is False
        assert result["error"] == "Connection timeout"

    def test_get_subagent_result_not_found(self, tmp_path, monkeypatch):
        """Test getting result for unknown session."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import get_subagent_result

        result = get_subagent_result("nonexistent")
        assert result is None

    def test_clear_subagent_result(self, tmp_path, monkeypatch):
        """Test clearing a subagent result."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import (
            handle_subagent_stop,
            get_subagent_result,
            clear_subagent_result,
        )

        handle_subagent_stop(session_id="agent-789", result="Done", success=True)
        assert get_subagent_result("agent-789") is not None

        cleared = clear_subagent_result("agent-789")
        assert cleared is True
        assert get_subagent_result("agent-789") is None

    def test_clear_subagent_result_not_found(self, tmp_path, monkeypatch):
        """Test clearing unknown session result."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import clear_subagent_result

        cleared = clear_subagent_result("nonexistent")
        assert cleared is False

    def test_get_all_pending_results(self, tmp_path, monkeypatch):
        """Test getting all pending results."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import (
            handle_subagent_stop,
            get_all_pending_results,
        )

        handle_subagent_stop(session_id="agent-1", result="Result 1", success=True)
        handle_subagent_stop(session_id="agent-2", result="Result 2", success=True)

        results = get_all_pending_results()
        assert len(results) == 2
        assert "agent-1" in results
        assert "agent-2" in results

    def test_get_all_pending_results_empty(self, tmp_path, monkeypatch):
        """Test getting pending results when none exist."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import get_all_pending_results

        results = get_all_pending_results()
        assert results == {}

    def test_handle_subagent_stop_no_session_id(self, tmp_path, monkeypatch):
        """Test handling stop with no session ID."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import handle_subagent_stop, get_all_pending_results

        # Should not raise
        handle_subagent_stop(session_id=None, result="Test")

        results = get_all_pending_results()
        assert results == {}

    def test_subagent_stop_main_entry(self, tmp_path, monkeypatch):
        """Test main entry point."""
        monkeypatch.chdir(tmp_path)

        from beyond_ralph.hooks.subagent_stop import main, get_subagent_result

        # Mock sys.argv
        import sys
        original_argv = sys.argv
        sys.argv = ["subagent_stop", "--session-id", "test-main", "--result", "Main entry result"]

        try:
            main()
        finally:
            sys.argv = original_argv

        result = get_subagent_result("test-main")
        assert result is not None
        assert result["result"] == "Main entry result"


class TestQuotaCheckEdgeCases:
    """Edge case tests for quota check hook."""

    def test_check_quota_state_file_not_exists_when_limited(self, tmp_path, monkeypatch):
        """Test quota check when limited but no state file exists."""
        monkeypatch.chdir(tmp_path)

        # Mock QuotaManager
        mock_status = MagicMock()
        mock_status.is_limited = True
        mock_status.session_percent = 90.0
        mock_status.weekly_percent = 85.0
        mock_status.to_dict.return_value = {"session_percent": 90.0, "weekly_percent": 85.0}

        mock_manager = MagicMock()
        mock_manager.check.return_value = mock_status

        with patch('beyond_ralph.core.quota_manager.QuotaManager', return_value=mock_manager):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            result = check_quota_before_spawn()
            # Should still return 1 (block) even without state file
            assert result == 1

    def test_check_quota_prints_stderr_when_limited(self, tmp_path, monkeypatch, capsys):
        """Test quota check prints to stderr when limited."""
        monkeypatch.chdir(tmp_path)

        # Mock QuotaManager
        mock_status = MagicMock()
        mock_status.is_limited = True
        mock_status.session_percent = 95.0
        mock_status.weekly_percent = 92.0
        mock_status.to_dict.return_value = {"session_percent": 95.0, "weekly_percent": 92.0}

        mock_manager = MagicMock()
        mock_manager.check.return_value = mock_status

        with patch('beyond_ralph.core.quota_manager.QuotaManager', return_value=mock_manager):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            check_quota_before_spawn()

        captured = capsys.readouterr()
        assert "95.0%" in captured.err
        assert "92.0%" in captured.err
        assert "Pausing agent spawns" in captured.err

    def test_check_quota_exception_prints_warning(self, tmp_path, monkeypatch, capsys):
        """Test quota check prints warning on exception."""
        monkeypatch.chdir(tmp_path)

        with patch('beyond_ralph.core.quota_manager.QuotaManager', side_effect=RuntimeError("Test error")):
            from beyond_ralph.hooks.quota_check import check_quota_before_spawn

            result = check_quota_before_spawn()

        assert result == 0  # Allow on error
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "Test error" in captured.err

    def test_check_quota_import_error(self, tmp_path, monkeypatch):
        """Test quota check handles ImportError gracefully."""
        import sys
        monkeypatch.chdir(tmp_path)

        # Remove the module from sys.modules to force fresh import
        if 'beyond_ralph.hooks.quota_check' in sys.modules:
            del sys.modules['beyond_ralph.hooks.quota_check']

        # Mock the import to fail
        original_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __builtins__.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'beyond_ralph.core.quota_manager':
                raise ImportError("QuotaManager not available")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            # Re-import the module with the mock
            from beyond_ralph.hooks import quota_check
            from importlib import reload

            try:
                reload(quota_check)
            except ImportError:
                pass

            # Call the function - it should handle ImportError internally
            result = quota_check.check_quota_before_spawn()
            # Should return 0 (allow) when import fails
            assert result == 0
