"""Unit tests for Notification System."""

import pytest

from beyond_ralph.core.notifications import (
    DiscordProvider,
    EmailProvider,
    NotificationChannel,
    NotificationLevel,
    NotificationManager,
    OSNotificationProvider,
    SlackProvider,
)


class TestNotificationLevel:
    """Tests for NotificationLevel enum."""

    def test_level_values(self) -> None:
        """Test all levels are defined."""
        assert NotificationLevel.INFO.value == "info"
        assert NotificationLevel.WARNING.value == "warning"
        assert NotificationLevel.ERROR.value == "error"
        assert NotificationLevel.BLOCKED.value == "blocked"
        assert NotificationLevel.COMPLETE.value == "complete"


class TestNotificationChannel:
    """Tests for NotificationChannel enum."""

    def test_channel_values(self) -> None:
        """Test all channels are defined."""
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.DISCORD.value == "discord"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.WHATSAPP.value == "whatsapp"
        assert NotificationChannel.OS.value == "os"


class TestSlackProvider:
    """Tests for SlackProvider."""

    def test_is_configured_with_url(self) -> None:
        """Test is_configured with URL set."""
        provider = SlackProvider("https://hooks.slack.com/test")
        assert provider.is_configured()

    def test_is_configured_without_url(self) -> None:
        """Test is_configured without URL."""
        provider = SlackProvider("")
        assert not provider.is_configured()


class TestDiscordProvider:
    """Tests for DiscordProvider."""

    def test_is_configured_with_url(self) -> None:
        """Test is_configured with URL set."""
        provider = DiscordProvider("https://discord.com/api/webhooks/test")
        assert provider.is_configured()

    def test_is_configured_without_url(self) -> None:
        """Test is_configured without URL."""
        provider = DiscordProvider("")
        assert not provider.is_configured()


class TestEmailProvider:
    """Tests for EmailProvider."""

    def test_is_configured_complete(self) -> None:
        """Test is_configured with all fields."""
        provider = EmailProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username="user@example.com",
            password="password",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )
        assert provider.is_configured()

    def test_is_configured_incomplete(self) -> None:
        """Test is_configured with missing fields."""
        provider = EmailProvider(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username="",
            password="",
            from_addr="",
            to_addr="",
        )
        assert not provider.is_configured()


class TestOSNotificationProvider:
    """Tests for OSNotificationProvider."""

    def test_is_configured_always_true(self) -> None:
        """Test OS notifications are always configured."""
        provider = OSNotificationProvider()
        assert provider.is_configured()


class TestNotificationManager:
    """Tests for NotificationManager."""

    def test_initialization(self) -> None:
        """Test manager initializes with no channels."""
        manager = NotificationManager()
        assert not manager.is_any_configured()
        assert len(manager.get_enabled_channels()) == 0

    def test_configure_slack(self) -> None:
        """Test configuring Slack channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": "https://hooks.slack.com/test"},
        )

        assert result
        assert manager.is_any_configured()
        assert NotificationChannel.SLACK in manager.get_enabled_channels()

    def test_configure_discord(self) -> None:
        """Test configuring Discord channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.DISCORD,
            {"webhook_url": "https://discord.com/api/webhooks/test"},
        )

        assert result
        assert NotificationChannel.DISCORD in manager.get_enabled_channels()

    def test_configure_os(self) -> None:
        """Test configuring OS channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.OS,
            {},
        )

        assert result
        assert NotificationChannel.OS in manager.get_enabled_channels()

    def test_configure_email_incomplete(self) -> None:
        """Test configuring Email with incomplete config fails."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.EMAIL,
            {"smtp_host": "smtp.gmail.com"},  # Missing other fields
        )

        assert not result
        assert NotificationChannel.EMAIL not in manager.get_enabled_channels()

    def test_disable_channel(self) -> None:
        """Test disabling a channel."""
        manager = NotificationManager()
        manager.configure_channel(
            NotificationChannel.OS,
            {},
        )

        assert NotificationChannel.OS in manager.get_enabled_channels()

        manager.disable_channel(NotificationChannel.OS)

        assert NotificationChannel.OS not in manager.get_enabled_channels()

    def test_enable_channel(self) -> None:
        """Test re-enabling a channel."""
        manager = NotificationManager()
        manager.configure_channel(
            NotificationChannel.OS,
            {},
        )
        manager.disable_channel(NotificationChannel.OS)

        result = manager.enable_channel(NotificationChannel.OS)

        assert result
        assert NotificationChannel.OS in manager.get_enabled_channels()

    def test_enable_unconfigured_channel(self) -> None:
        """Test enabling an unconfigured channel fails."""
        manager = NotificationManager()

        result = manager.enable_channel(NotificationChannel.SLACK)

        assert not result

    @pytest.mark.asyncio
    async def test_notify_no_channels(self) -> None:
        """Test notify with no configured channels."""
        manager = NotificationManager()

        results = await manager.notify("Test message")

        assert results == {}

    @pytest.mark.asyncio
    async def test_notify_specific_channel(self) -> None:
        """Test notify to specific channel."""
        manager = NotificationManager()
        manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": "https://hooks.slack.com/test"},
        )
        manager.configure_channel(
            NotificationChannel.OS,
            {},
        )

        # This will fail because webhook is fake, but tests the routing
        results = await manager.notify(
            "Test",
            channel=NotificationChannel.SLACK,
        )

        # Only Slack should be in results (even if it fails)
        assert NotificationChannel.SLACK in results
        assert NotificationChannel.OS not in results

    @pytest.mark.asyncio
    async def test_notify_blocked(self) -> None:
        """Test notify_blocked method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        results = await manager.notify_blocked("Needs user input")

        assert NotificationChannel.OS in results

    @pytest.mark.asyncio
    async def test_notify_error(self) -> None:
        """Test notify_error method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        results = await manager.notify_error("Something went wrong")

        assert NotificationChannel.OS in results

    @pytest.mark.asyncio
    async def test_notify_complete(self) -> None:
        """Test notify_complete method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        results = await manager.notify_complete("Project finished")

        assert NotificationChannel.OS in results

    @pytest.mark.asyncio
    async def test_notify_quota_pause(self) -> None:
        """Test notify_quota_pause method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        results = await manager.notify_quota_pause()

        assert NotificationChannel.OS in results
