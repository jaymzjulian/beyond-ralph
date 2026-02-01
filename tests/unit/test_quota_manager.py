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
