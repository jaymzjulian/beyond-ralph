"""Unit tests for Quota Manager."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.quota_manager import (
    QuotaManager,
    QuotaStatus,
)


@pytest.fixture
def temp_cache_file(tmp_path: Path) -> Path:
    """Create a temporary cache file path."""
    return tmp_path / "quota_cache"


@pytest.fixture
def quota_manager(temp_cache_file: Path) -> QuotaManager:
    """Create a quota manager with temp cache file."""
    return QuotaManager(cache_file=temp_cache_file)


class TestQuotaStatus:
    """Tests for QuotaStatus."""

    def test_status_level_green(self) -> None:
        """Test green status level."""
        status = QuotaStatus(
            session_percent=50.0,
            weekly_percent=40.0,
            checked_at=datetime.now(),
            is_limited=False,
        )
        assert status.status_level == "green"

    def test_status_level_yellow(self) -> None:
        """Test yellow status level."""
        status = QuotaStatus(
            session_percent=90.0,
            weekly_percent=40.0,
            checked_at=datetime.now(),
            is_limited=True,
        )
        assert status.status_level == "yellow"

    def test_status_level_red(self) -> None:
        """Test red status level."""
        status = QuotaStatus(
            session_percent=98.0,
            weekly_percent=40.0,
            checked_at=datetime.now(),
            is_limited=True,
        )
        assert status.status_level == "red"

    def test_to_dict(self) -> None:
        """Test converting to dict."""
        now = datetime.now()
        status = QuotaStatus(
            session_percent=75.0,
            weekly_percent=60.0,
            checked_at=now,
            is_limited=False,
        )

        data = status.to_dict()

        assert data["session_percent"] == 75.0
        assert data["weekly_percent"] == 60.0
        assert data["is_limited"] is False

    def test_from_dict(self) -> None:
        """Test creating from dict."""
        data = {
            "session_percent": 80.0,
            "weekly_percent": 50.0,
            "checked_at": "2024-02-01T10:00:00",
            "is_limited": False,
        }

        status = QuotaStatus.from_dict(data)

        assert status.session_percent == 80.0
        assert status.weekly_percent == 50.0
        assert not status.is_limited


class TestQuotaManager:
    """Tests for QuotaManager."""

    def test_threshold(self, quota_manager: QuotaManager) -> None:
        """Test threshold configuration."""
        assert quota_manager.threshold == 85

        custom = QuotaManager(threshold=90)
        assert custom.threshold == 90

    def test_is_limited_initially_false(self, quota_manager: QuotaManager) -> None:
        """Test is_limited starts false."""
        assert not quota_manager.is_limited()

    def test_cache_loading(self, quota_manager: QuotaManager, temp_cache_file: Path) -> None:
        """Test loading from cache."""
        # Write cache
        cache_data = {
            "session_percent": 50.0,
            "weekly_percent": 40.0,
            "checked_at": datetime.now().isoformat(),
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        # Load should use cache
        status = quota_manager._load_cache()
        assert status is not None
        assert status.session_percent == 50.0

    def test_cache_expiry(self, quota_manager: QuotaManager, temp_cache_file: Path) -> None:
        """Test cache expiry."""
        # Write old cache
        from datetime import timedelta

        old_time = datetime.now() - timedelta(minutes=10)
        cache_data = {
            "session_percent": 50.0,
            "weekly_percent": 40.0,
            "checked_at": old_time.isoformat(),
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        # Cache should be expired
        status = quota_manager._load_cache()
        assert status is None

    def test_cache_save(self, quota_manager: QuotaManager, temp_cache_file: Path) -> None:
        """Test saving to cache."""
        status = QuotaStatus(
            session_percent=70.0,
            weekly_percent=55.0,
            checked_at=datetime.now(),
            is_limited=False,
        )

        quota_manager._save_cache(status)

        assert temp_cache_file.exists()
        data = json.loads(temp_cache_file.read_text())
        assert data["session_percent"] == 70.0

    @pytest.mark.asyncio
    async def test_pre_spawn_check_allows(self, quota_manager: QuotaManager, temp_cache_file: Path) -> None:
        """Test pre-spawn check allows when under threshold."""
        # Write cache under threshold
        cache_data = {
            "session_percent": 50.0,
            "weekly_percent": 40.0,
            "checked_at": datetime.now().isoformat(),
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        allowed = await quota_manager.pre_spawn_check()
        assert allowed

    @pytest.mark.asyncio
    async def test_pre_spawn_check_blocks(self, quota_manager: QuotaManager, temp_cache_file: Path) -> None:
        """Test pre-spawn check blocks when over threshold."""
        # Write cache over threshold
        cache_data = {
            "session_percent": 90.0,
            "weekly_percent": 40.0,
            "checked_at": datetime.now().isoformat(),
            "is_limited": True,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        allowed = await quota_manager.pre_spawn_check()
        assert not allowed

    def test_get_summary(self, quota_manager: QuotaManager) -> None:
        """Test getting summary."""
        summary = quota_manager.get_summary()

        assert "session_percent" in summary
        assert "weekly_percent" in summary
        assert "status" in summary
        assert "is_limited" in summary

    def test_get_summary_with_status(self, quota_manager: QuotaManager) -> None:
        """Test getting summary when status exists."""
        quota_manager._last_status = QuotaStatus(
            session_percent=75.0,
            weekly_percent=60.0,
            checked_at=datetime.now(),
            is_limited=False,
        )

        summary = quota_manager.get_summary()

        assert summary["session_percent"] == 75.0
        assert summary["weekly_percent"] == 60.0
        assert summary["status"] == "green"
        assert summary["is_limited"] is False
        assert "checked_at" in summary


class TestQuotaManagerCLICheck:
    """Tests for CLI-based quota checking."""

    @pytest.mark.asyncio
    async def test_check_via_cli_claude_not_found(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli when Claude is not installed."""
        from unittest.mock import patch
        import subprocess

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            status = await manager._check_via_cli()

            # Should return zero values when CLI not found
            assert status.session_percent == 0.0
            assert status.weekly_percent == 0.0
            assert not status.is_limited

    @pytest.mark.asyncio
    async def test_check_via_cli_timeout(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli when CLI times out."""
        from unittest.mock import patch, MagicMock
        import subprocess

        manager = QuotaManager(cache_file=temp_cache_file)

        # Set a previous status
        manager._last_status = QuotaStatus(
            session_percent=50.0,
            weekly_percent=40.0,
            checked_at=datetime.now(),
            is_limited=False,
        )

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)
            status = await manager._check_via_cli()

            # Should keep last known values
            assert status.session_percent == 50.0
            assert status.weekly_percent == 40.0

    @pytest.mark.asyncio
    async def test_check_via_cli_parses_session(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli parses session percentage."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 75.5%\nWeekly usage: 45%\n"
            )
            status = await manager._check_via_cli()

            assert status.session_percent == 75.5
            assert status.weekly_percent == 45.0

    @pytest.mark.asyncio
    async def test_check_via_cli_is_limited(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli marks as limited when over threshold."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 90%\nWeekly usage: 45%\n"
            )
            status = await manager._check_via_cli()

            assert status.is_limited is True


class TestQuotaManagerCheck:
    """Tests for the check() method."""

    @pytest.mark.asyncio
    async def test_check_uses_cache(self, temp_cache_file: Path) -> None:
        """Test check uses cache when available."""
        manager = QuotaManager(cache_file=temp_cache_file)

        # Write valid cache
        cache_data = {
            "session_percent": 60.0,
            "weekly_percent": 45.0,
            "checked_at": datetime.now().isoformat(),
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        status = await manager.check()

        assert status.session_percent == 60.0
        assert manager._paused is False

    @pytest.mark.asyncio
    async def test_check_force_refresh(self, temp_cache_file: Path) -> None:
        """Test check with force_refresh bypasses cache."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        # Write cache (would normally be used)
        cache_data = {
            "session_percent": 60.0,
            "weekly_percent": 45.0,
            "checked_at": datetime.now().isoformat(),
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 80%\nWeekly usage: 50%\n"
            )
            status = await manager.check(force_refresh=True)

            # Should use CLI result, not cache
            assert status.session_percent == 80.0


class TestQuotaManagerCacheErrors:
    """Tests for cache error handling."""

    def test_load_cache_invalid_json(self, temp_cache_file: Path) -> None:
        """Test loading cache with invalid JSON."""
        manager = QuotaManager(cache_file=temp_cache_file)

        temp_cache_file.write_text("not valid json")

        status = manager._load_cache()
        assert status is None

    def test_load_cache_missing_key(self, temp_cache_file: Path) -> None:
        """Test loading cache with missing keys."""
        manager = QuotaManager(cache_file=temp_cache_file)

        temp_cache_file.write_text('{"session_percent": 50}')  # Missing other keys

        status = manager._load_cache()
        assert status is None

    def test_load_cache_file_not_exists(self, temp_cache_file: Path) -> None:
        """Test loading cache when file doesn't exist."""
        manager = QuotaManager(cache_file=temp_cache_file)

        # Don't create the file
        status = manager._load_cache()
        assert status is None


class TestQuotaConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_check_quota_function(self) -> None:
        """Test check_quota convenience function."""
        from unittest.mock import patch, MagicMock
        from beyond_ralph.core.quota_manager import check_quota, _quota_manager
        import beyond_ralph.core.quota_manager as qm

        # Reset singleton
        qm._quota_manager = None

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 50%\nWeekly usage: 30%\n"
            )
            allowed = await check_quota()

            assert allowed is True

    def test_get_quota_manager_singleton(self) -> None:
        """Test get_quota_manager returns singleton."""
        from beyond_ralph.core.quota_manager import get_quota_manager
        import beyond_ralph.core.quota_manager as qm

        # Reset singleton
        qm._quota_manager = None

        manager1 = get_quota_manager()
        manager2 = get_quota_manager()

        assert manager1 is manager2


class TestQuotaManagerCLIEdgeCases:
    """Tests for CLI edge cases in quota checking."""

    @pytest.mark.asyncio
    async def test_check_via_cli_rmtree_exception(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli handles rmtree exception gracefully."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run, \
             patch("shutil.rmtree") as mock_rmtree:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 50%\nWeekly usage: 40%\n"
            )
            mock_rmtree.side_effect = PermissionError("Cannot delete")

            # Should still succeed despite rmtree failure
            status = await manager._check_via_cli()

            assert status.session_percent == 50.0
            assert status.weekly_percent == 40.0

    @pytest.mark.asyncio
    async def test_check_via_cli_invalid_session_format(
        self, temp_cache_file: Path
    ) -> None:
        """Test _check_via_cli handles invalid session format."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            # Session line without valid number
            mock_run.return_value = MagicMock(
                stdout="Session usage: invalid%\nWeekly usage: 40%\n"
            )
            status = await manager._check_via_cli()

            # Session should be 0 due to parse failure
            assert status.session_percent == 0.0
            assert status.weekly_percent == 40.0

    @pytest.mark.asyncio
    async def test_check_via_cli_invalid_weekly_format(
        self, temp_cache_file: Path
    ) -> None:
        """Test _check_via_cli handles invalid weekly format."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            # Weekly line without valid number
            mock_run.return_value = MagicMock(
                stdout="Session usage: 50%\nWeekly usage: not_a_number%\n"
            )
            status = await manager._check_via_cli()

            assert status.session_percent == 50.0
            # Weekly should be 0 due to parse failure
            assert status.weekly_percent == 0.0

    @pytest.mark.asyncio
    async def test_check_via_cli_no_percent_sign(self, temp_cache_file: Path) -> None:
        """Test _check_via_cli handles missing percent sign."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            # Lines without % sign
            mock_run.return_value = MagicMock(
                stdout="Session usage: 50\nWeekly usage: 40\n"
            )
            status = await manager._check_via_cli()

            # Should be 0 because % wasn't found in line
            assert status.session_percent == 0.0
            assert status.weekly_percent == 0.0


class TestQuotaManagerWaitForReset:
    """Tests for wait_for_reset method."""

    @pytest.mark.asyncio
    async def test_wait_for_reset_immediate_return(
        self, temp_cache_file: Path
    ) -> None:
        """Test wait_for_reset returns immediately when not limited."""
        from unittest.mock import patch, MagicMock

        manager = QuotaManager(cache_file=temp_cache_file)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Session usage: 50%\nWeekly usage: 40%\n"
            )

            # Should return immediately since not limited
            await manager.wait_for_reset()

            assert manager._paused is False

    @pytest.mark.asyncio
    async def test_wait_for_reset_waits_then_returns(
        self, temp_cache_file: Path
    ) -> None:
        """Test wait_for_reset waits and checks again."""
        from unittest.mock import patch, MagicMock, AsyncMock

        manager = QuotaManager(cache_file=temp_cache_file)

        call_count = 0

        def mock_cli_check(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: limited
                return MagicMock(stdout="Session usage: 90%\nWeekly usage: 40%\n")
            else:
                # Second call: no longer limited
                return MagicMock(stdout="Session usage: 50%\nWeekly usage: 40%\n")

        with patch("subprocess.run", side_effect=mock_cli_check), \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await manager.wait_for_reset()

            # Should have slept once (10 minutes)
            mock_sleep.assert_called_once_with(600)
            assert manager._paused is False
            assert call_count == 2


class TestQuotaManagerCacheEdgeCases:
    """Tests for cache edge cases."""

    def test_load_cache_paused_uses_longer_cache(
        self, temp_cache_file: Path
    ) -> None:
        """Test that paused state uses longer cache duration."""
        from datetime import timedelta

        manager = QuotaManager(cache_file=temp_cache_file)

        # Write cache that is 7 minutes old and limited
        # Normal cache expires at 5 mins, paused cache at 10 mins
        old_time = datetime.now() - timedelta(minutes=7)
        cache_data = {
            "session_percent": 90.0,
            "weekly_percent": 40.0,
            "checked_at": old_time.isoformat(),
            "is_limited": True,  # Paused state
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        # Should still be valid (7 min < 10 min paused cache)
        status = manager._load_cache()
        assert status is not None
        assert status.session_percent == 90.0

    def test_load_cache_invalid_date_format(self, temp_cache_file: Path) -> None:
        """Test loading cache with invalid date format."""
        manager = QuotaManager(cache_file=temp_cache_file)

        cache_data = {
            "session_percent": 50.0,
            "weekly_percent": 40.0,
            "checked_at": "not-a-valid-date",
            "is_limited": False,
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        # Should return None due to ValueError in date parsing
        status = manager._load_cache()
        assert status is None


class TestQuotaStatusEdgeCases:
    """Tests for QuotaStatus edge cases."""

    def test_status_level_weekly_over_session(self) -> None:
        """Test status level uses max of session and weekly."""
        status = QuotaStatus(
            session_percent=50.0,
            weekly_percent=95.0,  # Weekly is higher
            checked_at=datetime.now(),
            is_limited=True,
        )
        # Should be red because weekly is >= 95
        assert status.status_level == "red"

    def test_status_level_exactly_at_thresholds(self) -> None:
        """Test status level at exact threshold boundaries."""
        # Exactly 85%
        status_yellow = QuotaStatus(
            session_percent=85.0,
            weekly_percent=50.0,
            checked_at=datetime.now(),
            is_limited=True,
        )
        assert status_yellow.status_level == "yellow"

        # Exactly 95%
        status_red = QuotaStatus(
            session_percent=95.0,
            weekly_percent=50.0,
            checked_at=datetime.now(),
            is_limited=True,
        )
        assert status_red.status_level == "red"

        # Just under 85% (84.9%)
        status_green = QuotaStatus(
            session_percent=84.9,
            weekly_percent=50.0,
            checked_at=datetime.now(),
            is_limited=False,
        )
        assert status_green.status_level == "green"
