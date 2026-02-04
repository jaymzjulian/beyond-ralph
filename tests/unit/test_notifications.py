"""Tests for notifications module."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beyond_ralph.core.notifications import (
    NotificationChannel,
    NotificationConfig,
    NotificationLevel,
    NotificationManager,
    SlackProvider,
    DiscordProvider,
    EmailProvider,
    OSNotificationProvider,
    get_notification_manager,
    configure_from_env,
)


class TestNotificationLevel:
    """Tests for NotificationLevel enum."""

    def test_notification_levels(self):
        """Test all notification levels exist."""
        assert NotificationLevel.INFO.value == "info"
        assert NotificationLevel.WARNING.value == "warning"
        assert NotificationLevel.ERROR.value == "error"
        assert NotificationLevel.BLOCKED.value == "blocked"
        assert NotificationLevel.COMPLETE.value == "complete"


class TestNotificationChannel:
    """Tests for NotificationChannel enum."""

    def test_notification_channels(self):
        """Test all notification channels exist."""
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.DISCORD.value == "discord"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.WHATSAPP.value == "whatsapp"
        assert NotificationChannel.OS.value == "os"


class TestNotificationConfig:
    """Tests for NotificationConfig dataclass."""

    def test_config_creation(self):
        """Test creating notification config."""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            credentials={"webhook_url": "https://hooks.slack.com/xxx"},
        )

        assert config.channel == NotificationChannel.SLACK
        assert config.enabled is True
        assert config.credentials["webhook_url"] == "https://hooks.slack.com/xxx"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "type": "discord",
            "enabled": True,
            "credentials": {"webhook_url": "https://discord.com/xxx"},
        }

        config = NotificationConfig.from_dict(data)

        assert config.channel == NotificationChannel.DISCORD
        assert config.enabled is True
        assert config.credentials["webhook_url"] == "https://discord.com/xxx"

    def test_config_from_dict_defaults(self):
        """Test config from dict with missing optional fields."""
        data = {"type": "os"}

        config = NotificationConfig.from_dict(data)

        assert config.channel == NotificationChannel.OS
        assert config.enabled is True  # Default
        assert config.credentials == {}  # Default


class TestSlackProvider:
    """Tests for SlackProvider."""

    def test_is_configured_with_url(self):
        """Test provider is configured with webhook URL."""
        provider = SlackProvider(webhook_url="https://hooks.slack.com/xxx")
        assert provider.is_configured() is True

    def test_is_configured_without_url(self):
        """Test provider is not configured without URL."""
        provider = SlackProvider(webhook_url="")
        assert provider.is_configured() is False

    @pytest.mark.asyncio
    async def test_send_not_configured(self):
        """Test send returns False when not configured."""
        provider = SlackProvider(webhook_url="")
        result = await provider.send("test message", NotificationLevel.INFO)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Test successful send."""
        provider = SlackProvider(webhook_url="https://hooks.slack.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.INFO)
            assert result is True


class TestDiscordProvider:
    """Tests for DiscordProvider."""

    def test_is_configured_with_url(self):
        """Test provider is configured with webhook URL."""
        provider = DiscordProvider(webhook_url="https://discord.com/xxx")
        assert provider.is_configured() is True

    def test_is_configured_without_url(self):
        """Test provider is not configured without URL."""
        provider = DiscordProvider(webhook_url="")
        assert provider.is_configured() is False

    @pytest.mark.asyncio
    async def test_send_not_configured(self):
        """Test send returns False when not configured."""
        provider = DiscordProvider(webhook_url="")
        result = await provider.send("test message", NotificationLevel.INFO)
        assert result is False


class TestEmailProvider:
    """Tests for EmailProvider."""

    def test_is_configured_all_fields(self):
        """Test provider is configured with all fields."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )
        assert provider.is_configured() is True

    def test_is_configured_missing_fields(self):
        """Test provider is not configured with missing fields."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )
        assert provider.is_configured() is False

    @pytest.mark.asyncio
    async def test_send_not_configured(self):
        """Test send returns False when not configured."""
        provider = EmailProvider(
            smtp_host="",
            smtp_port=587,
            username="",
            password="",
            from_addr="",
            to_addr="",
        )
        result = await provider.send("test message", NotificationLevel.INFO)
        assert result is False


class TestOSNotificationProvider:
    """Tests for OSNotificationProvider."""

    def test_is_configured_always_true(self):
        """Test OS notifications are always configured."""
        provider = OSNotificationProvider()
        assert provider.is_configured() is True

    @pytest.mark.asyncio
    async def test_send_linux(self):
        """Test send on Linux."""
        provider = OSNotificationProvider()

        with patch("sys.platform", "linux"):
            with patch("subprocess.run") as mock_run:
                result = await provider.send("test message", NotificationLevel.INFO)
                assert result is True
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_macos(self):
        """Test send on macOS."""
        provider = OSNotificationProvider()

        with patch("sys.platform", "darwin"):
            with patch("subprocess.run") as mock_run:
                result = await provider.send("test message", NotificationLevel.INFO)
                assert result is True
                mock_run.assert_called_once()


class TestNotificationManager:
    """Tests for NotificationManager."""

    def test_manager_creation(self):
        """Test manager creation."""
        manager = NotificationManager()
        assert manager.is_any_configured() is False
        assert manager.get_enabled_channels() == []

    def test_configure_slack_channel(self):
        """Test configuring Slack channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": "https://hooks.slack.com/test"},
        )
        assert result is True
        assert NotificationChannel.SLACK in manager.get_enabled_channels()

    def test_configure_discord_channel(self):
        """Test configuring Discord channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.DISCORD,
            {"webhook_url": "https://discord.com/test"},
        )
        assert result is True
        assert NotificationChannel.DISCORD in manager.get_enabled_channels()

    def test_configure_os_channel(self):
        """Test configuring OS channel."""
        manager = NotificationManager()
        result = manager.configure_channel(NotificationChannel.OS, {})
        assert result is True
        assert NotificationChannel.OS in manager.get_enabled_channels()

    def test_configure_incomplete_channel(self):
        """Test configuring incomplete channel fails."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": ""},  # Empty URL
        )
        assert result is False

    def test_disable_channel(self):
        """Test disabling a channel."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})
        assert NotificationChannel.OS in manager.get_enabled_channels()

        manager.disable_channel(NotificationChannel.OS)
        assert NotificationChannel.OS not in manager.get_enabled_channels()

    def test_enable_channel(self):
        """Test enabling a previously configured channel."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})
        manager.disable_channel(NotificationChannel.OS)

        result = manager.enable_channel(NotificationChannel.OS)
        assert result is True
        assert NotificationChannel.OS in manager.get_enabled_channels()

    def test_enable_unconfigured_channel(self):
        """Test enabling unconfigured channel fails."""
        manager = NotificationManager()
        result = manager.enable_channel(NotificationChannel.SLACK)
        assert result is False

    @pytest.mark.asyncio
    async def test_notify_no_channels(self):
        """Test notify with no channels configured."""
        manager = NotificationManager()
        results = await manager.notify("test", NotificationLevel.INFO)
        assert results == {}

    @pytest.mark.asyncio
    async def test_notify_specific_channel(self):
        """Test notify to specific channel."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            results = await manager.notify(
                "test",
                NotificationLevel.INFO,
                channel=NotificationChannel.OS,
            )
            assert NotificationChannel.OS in results
            assert results[NotificationChannel.OS] is True

    @pytest.mark.asyncio
    async def test_notify_blocked(self):
        """Test notify_blocked method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            results = await manager.notify_blocked("Need user input")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "BLOCKED" in call_args[0][0]
            assert call_args[0][1] == NotificationLevel.BLOCKED

    @pytest.mark.asyncio
    async def test_notify_error(self):
        """Test notify_error method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            results = await manager.notify_error("Something failed")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "ERROR" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_notify_complete(self):
        """Test notify_complete method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            results = await manager.notify_complete("All done!")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "COMPLETE" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_notify_quota_pause(self):
        """Test notify_quota_pause method."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            results = await manager.notify_quota_pause()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "PAUSED" in call_args[0][0]


class TestGetNotificationManager:
    """Tests for get_notification_manager singleton."""

    def test_get_notification_manager_returns_instance(self):
        """Test singleton returns instance."""
        # Reset singleton
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        manager = get_notification_manager()
        assert isinstance(manager, NotificationManager)

    def test_get_notification_manager_returns_same_instance(self):
        """Test singleton returns same instance."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        manager1 = get_notification_manager()
        manager2 = get_notification_manager()
        assert manager1 is manager2


class TestSlackProviderSendPaths:
    """Additional tests for SlackProvider send paths."""

    @pytest.mark.asyncio
    async def test_send_exception_handling(self):
        """Test send handles exceptions gracefully."""
        provider = SlackProvider(webhook_url="https://hooks.slack.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = Exception("Network error")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.INFO)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_non_200_status(self):
        """Test send returns False for non-200 status."""
        provider = SlackProvider(webhook_url="https://hooks.slack.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.ERROR)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_all_levels(self):
        """Test send with all notification levels."""
        provider = SlackProvider(webhook_url="https://hooks.slack.com/test")

        for level in NotificationLevel:
            with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200

                mock_instance = AsyncMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None

                mock_client.return_value = mock_instance

                result = await provider.send("test", level)
                assert result is True


class TestDiscordProviderSendPaths:
    """Additional tests for DiscordProvider send paths."""

    @pytest.mark.asyncio
    async def test_send_success_200(self):
        """Test successful send with 200 status."""
        provider = DiscordProvider(webhook_url="https://discord.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.INFO)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_success_204(self):
        """Test successful send with 204 status."""
        provider = DiscordProvider(webhook_url="https://discord.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 204

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.WARNING)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_exception_handling(self):
        """Test send handles exceptions gracefully."""
        provider = DiscordProvider(webhook_url="https://discord.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = Exception("Connection timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.ERROR)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_non_success_status(self):
        """Test send returns False for error status."""
        provider = DiscordProvider(webhook_url="https://discord.com/test")

        with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429  # Rate limited

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            mock_client.return_value = mock_instance

            result = await provider.send("test message", NotificationLevel.BLOCKED)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_all_levels(self):
        """Test send with all notification levels."""
        provider = DiscordProvider(webhook_url="https://discord.com/test")

        for level in NotificationLevel:
            with patch("beyond_ralph.core.notifications.httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 204

                mock_instance = AsyncMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None

                mock_client.return_value = mock_instance

                result = await provider.send("test", level)
                assert result is True


class TestEmailProviderSendPaths:
    """Additional tests for EmailProvider send paths."""

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Test successful email send."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )

        with patch.object(provider, "_send_smtp") as mock_smtp:
            result = await provider.send("test message", NotificationLevel.INFO)
            assert result is True
            mock_smtp.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_exception_handling(self):
        """Test send handles exceptions gracefully."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )

        with patch.object(provider, "_send_smtp") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP connection failed")
            result = await provider.send("test message", NotificationLevel.ERROR)
            assert result is False

    def test_send_smtp_method(self):
        """Test _send_smtp method."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )

        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["From"] = "from@example.com"
        msg["To"] = "to@example.com"
        msg["Subject"] = "Test"

        with patch("beyond_ralph.core.notifications.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            provider._send_smtp(msg)

            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user", "pass")
            mock_server.send_message.assert_called_once_with(msg)

    @pytest.mark.asyncio
    async def test_send_all_levels(self):
        """Test send with all notification levels."""
        provider = EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            from_addr="from@example.com",
            to_addr="to@example.com",
        )

        for level in NotificationLevel:
            with patch.object(provider, "_send_smtp"):
                result = await provider.send("test", level)
                assert result is True


class TestOSNotificationProviderSendPaths:
    """Additional tests for OSNotificationProvider send paths."""

    @pytest.mark.asyncio
    async def test_send_windows(self):
        """Test send on Windows."""
        provider = OSNotificationProvider()

        with patch("sys.platform", "win32"):
            with patch("subprocess.run") as mock_run:
                result = await provider.send("test message", NotificationLevel.INFO)
                assert result is True
                mock_run.assert_called_once()
                # Verify powershell is called
                args = mock_run.call_args[0][0]
                assert args[0] == "powershell"

    @pytest.mark.asyncio
    async def test_send_exception_handling(self):
        """Test send handles exceptions gracefully."""
        provider = OSNotificationProvider()

        with patch("sys.platform", "linux"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Subprocess failed")
                result = await provider.send("test message", NotificationLevel.ERROR)
                assert result is False

    @pytest.mark.asyncio
    async def test_send_unknown_platform(self):
        """Test send on unknown platform."""
        provider = OSNotificationProvider()

        with patch("sys.platform", "freebsd"):
            # Should not crash, just return True without calling subprocess
            result = await provider.send("test message", NotificationLevel.INFO)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_all_levels(self):
        """Test send with all notification levels on each platform."""
        provider = OSNotificationProvider()

        for platform in ["darwin", "linux", "win32"]:
            for level in NotificationLevel:
                with patch("sys.platform", platform):
                    with patch("subprocess.run"):
                        result = await provider.send("test", level)
                        assert result is True


class TestNotificationManagerAdvanced:
    """Advanced tests for NotificationManager."""

    def test_configure_email_channel(self):
        """Test configuring Email channel."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.EMAIL,
            {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "username": "user",
                "password": "pass",
                "from_addr": "from@example.com",
                "to_addr": "to@example.com",
            },
        )
        assert result is True
        assert NotificationChannel.EMAIL in manager.get_enabled_channels()

    def test_configure_email_incomplete(self):
        """Test configuring Email channel with missing fields."""
        manager = NotificationManager()
        result = manager.configure_channel(
            NotificationChannel.EMAIL,
            {
                "smtp_host": "smtp.example.com",
                # Missing other required fields
            },
        )
        assert result is False

    def test_configure_unknown_channel(self):
        """Test configuring unknown channel type."""
        manager = NotificationManager()
        # WhatsApp is defined but not implemented
        result = manager.configure_channel(
            NotificationChannel.WHATSAPP,
            {"api_key": "test"},
        )
        assert result is False

    def test_configure_channel_exception(self):
        """Test configure_channel handles exceptions."""
        manager = NotificationManager()

        with patch.object(SlackProvider, "__init__") as mock_init:
            mock_init.side_effect = Exception("Init failed")
            result = manager.configure_channel(
                NotificationChannel.SLACK,
                {"webhook_url": "https://hooks.slack.com/test"},
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_notify_to_disabled_specific_channel(self):
        """Test notify to disabled specific channel."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})
        manager.disable_channel(NotificationChannel.OS)

        results = await manager.notify(
            "test",
            NotificationLevel.INFO,
            channel=NotificationChannel.OS,
        )
        assert results == {}

    @pytest.mark.asyncio
    async def test_notify_to_unconfigured_specific_channel(self):
        """Test notify to unconfigured specific channel."""
        manager = NotificationManager()

        results = await manager.notify(
            "test",
            NotificationLevel.INFO,
            channel=NotificationChannel.SLACK,
        )
        assert results == {}

    @pytest.mark.asyncio
    async def test_notify_all_enabled_channels(self):
        """Test notify sends to all enabled channels."""
        manager = NotificationManager()
        manager.configure_channel(NotificationChannel.OS, {})
        manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": "https://hooks.slack.com/test"},
        )

        with patch.object(OSNotificationProvider, "send", new_callable=AsyncMock) as mock_os:
            with patch.object(SlackProvider, "send", new_callable=AsyncMock) as mock_slack:
                mock_os.return_value = True
                mock_slack.return_value = True

                results = await manager.notify("test", NotificationLevel.INFO)

                assert NotificationChannel.OS in results
                assert NotificationChannel.SLACK in results
                assert results[NotificationChannel.OS] is True
                assert results[NotificationChannel.SLACK] is True


class TestConfigureFromEnv:
    """Tests for configure_from_env function."""

    def test_configure_from_env_slack(self, monkeypatch):
        """Test configuring from SLACK env var."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        monkeypatch.setenv("BEYOND_RALPH_SLACK_WEBHOOK", "https://hooks.slack.com/test")

        manager = configure_from_env()

        assert NotificationChannel.SLACK in manager.get_enabled_channels()

    def test_configure_from_env_discord(self, monkeypatch):
        """Test configuring from DISCORD env var."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        monkeypatch.setenv("BEYOND_RALPH_DISCORD_WEBHOOK", "https://discord.com/test")

        manager = configure_from_env()

        assert NotificationChannel.DISCORD in manager.get_enabled_channels()

    def test_configure_from_env_os_always(self, monkeypatch):
        """Test OS notifications always configured."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        # Clear any webhook env vars
        monkeypatch.delenv("BEYOND_RALPH_SLACK_WEBHOOK", raising=False)
        monkeypatch.delenv("BEYOND_RALPH_DISCORD_WEBHOOK", raising=False)

        manager = configure_from_env()

        assert NotificationChannel.OS in manager.get_enabled_channels()

    def test_configure_from_env_email(self, monkeypatch):
        """Test configuring from EMAIL env vars."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        monkeypatch.setenv("BEYOND_RALPH_SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("BEYOND_RALPH_SMTP_PORT", "587")
        monkeypatch.setenv("BEYOND_RALPH_SMTP_USER", "user")
        monkeypatch.setenv("BEYOND_RALPH_SMTP_PASS", "pass")
        monkeypatch.setenv("BEYOND_RALPH_EMAIL_FROM", "from@example.com")
        monkeypatch.setenv("BEYOND_RALPH_EMAIL_TO", "to@example.com")

        manager = configure_from_env()

        assert NotificationChannel.EMAIL in manager.get_enabled_channels()

    def test_configure_from_env_email_incomplete(self, monkeypatch):
        """Test configuring from incomplete EMAIL env vars."""
        import beyond_ralph.core.notifications as n
        n._notification_manager = None

        # Only set host, missing other fields
        monkeypatch.setenv("BEYOND_RALPH_SMTP_HOST", "smtp.example.com")
        monkeypatch.delenv("BEYOND_RALPH_SMTP_USER", raising=False)
        monkeypatch.delenv("BEYOND_RALPH_SMTP_PASS", raising=False)
        monkeypatch.delenv("BEYOND_RALPH_EMAIL_FROM", raising=False)
        monkeypatch.delenv("BEYOND_RALPH_EMAIL_TO", raising=False)

        manager = configure_from_env()

        # Email should not be configured due to missing fields
        assert NotificationChannel.EMAIL not in manager.get_enabled_channels()
