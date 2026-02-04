"""Live integration tests for quota checker.

These tests actually invoke the Claude CLI to verify quota checking works.
They have no harmful side effects - just reading quota status.
"""

from __future__ import annotations

import pytest

from beyond_ralph.utils.quota_checker import (
    QuotaStatus,
    check_quota_via_cli,
    check_quota_via_print_mode,
    get_quota_status,
)


class TestLiveQuotaChecker:
    """Live tests for quota checker against real Claude CLI."""

    @pytest.mark.integration
    def test_check_quota_via_cli_returns_status(self):
        """Test check_quota_via_cli returns a QuotaStatus."""
        status = check_quota_via_cli()

        assert isinstance(status, QuotaStatus)
        # Should have checked_at set
        assert status.checked_at is not None

    @pytest.mark.integration
    def test_check_quota_via_cli_valid_percentages(self):
        """Test CLI check returns valid percentages or unknown."""
        status = check_quota_via_cli()

        if not status.is_unknown:
            # If we got valid data, percentages should be in range
            assert 0 <= status.session_percent <= 100
            assert 0 <= status.weekly_percent <= 100
        else:
            # Unknown status should have -1 values
            assert status.session_percent == -1
            assert status.weekly_percent == -1
            # Should have an error message explaining why
            assert status.error_message is not None

    @pytest.mark.integration
    def test_check_quota_via_print_mode_returns_status(self):
        """Test check_quota_via_print_mode returns a QuotaStatus."""
        status = check_quota_via_print_mode()

        assert isinstance(status, QuotaStatus)
        assert status.checked_at is not None

    @pytest.mark.integration
    def test_get_quota_status_returns_status(self):
        """Test get_quota_status returns usable status."""
        status = get_quota_status(force_refresh=True)

        assert isinstance(status, QuotaStatus)

        # Status should have valid is_limited and can_proceed
        assert isinstance(status.is_limited, bool)
        assert isinstance(status.can_proceed, bool)

        # is_limited and can_proceed should be logically consistent
        if status.is_unknown:
            # Unknown = blocked (fail-safe)
            assert status.can_proceed is False
        elif status.is_limited:
            # Limited = blocked
            assert status.can_proceed is False
        else:
            # Not limited = can proceed
            assert status.can_proceed is True

    @pytest.mark.integration
    def test_quota_status_color_valid(self):
        """Test status color is valid."""
        status = get_quota_status(force_refresh=True)

        # Color should be one of the valid options
        assert status.status_color in ["green", "yellow", "red"]

    @pytest.mark.integration
    def test_quota_to_dict_serializable(self):
        """Test quota status can be serialized."""
        import json

        status = get_quota_status(force_refresh=True)
        data = status.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert json_str is not None

        # Should round-trip
        restored = json.loads(json_str)
        assert restored["session_percent"] == status.session_percent
        assert restored["weekly_percent"] == status.weekly_percent

    @pytest.mark.integration
    def test_quota_caching_works(self, tmp_path, monkeypatch):
        """Test quota caching saves and loads."""
        from beyond_ralph.utils.quota_checker import (
            load_cached_quota,
            save_quota_cache,
        )

        monkeypatch.chdir(tmp_path)

        # Get fresh status
        status = get_quota_status(force_refresh=True)

        if not status.is_unknown:
            # Save to cache
            save_quota_cache(status)

            # Load from cache
            cached = load_cached_quota()

            assert cached is not None
            assert cached.session_percent == status.session_percent
            assert cached.weekly_percent == status.weekly_percent


class TestLiveQuotaDisplay:
    """Live tests for quota display functionality."""

    @pytest.mark.integration
    def test_check_and_display_quota_runs(self, capsys):
        """Test check_and_display_quota runs without error."""
        from beyond_ralph.utils.quota_checker import check_and_display_quota

        # Should not raise
        check_and_display_quota()

        # Should produce some output
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        # Should contain quota-related info
        assert "%" in captured.out or "Session" in captured.out or "ERROR" in captured.out
