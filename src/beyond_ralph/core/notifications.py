"""Notification System for Beyond Ralph.

Provides remote notifications for unsupervised operation.
Only sends notifications when blocked or needs user input.
"""

import asyncio
import json
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKED = "blocked"  # Needs user input
    COMPLETE = "complete"


class NotificationChannel(Enum):
    """Available notification channels."""

    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    OS = "os"  # Native OS notifications


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""

    channel: NotificationChannel
    enabled: bool = True
    credentials: dict[str, str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationConfig":
        """Create from dictionary."""
        return cls(
            channel=NotificationChannel(data["type"]),
            enabled=data.get("enabled", True),
            credentials=data.get("credentials", {}),
        )


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, message: str, level: NotificationLevel) -> bool:
        """Send a notification.

        Args:
            message: The notification message.
            level: Severity level.

        Returns:
            True if sent successfully.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this provider is properly configured."""
        pass


class SlackProvider(NotificationProvider):
    """Slack webhook notifications."""

    def __init__(self, webhook_url: str):
        """Initialize Slack provider.

        Args:
            webhook_url: Slack incoming webhook URL.
        """
        self.webhook_url = webhook_url

    def is_configured(self) -> bool:
        """Check if webhook URL is set."""
        return bool(self.webhook_url)

    async def send(self, message: str, level: NotificationLevel) -> bool:
        """Send notification via Slack webhook."""
        if not self.is_configured():
            return False

        # Color based on level
        colors = {
            NotificationLevel.INFO: "#36a64f",
            NotificationLevel.WARNING: "#ffcc00",
            NotificationLevel.ERROR: "#ff0000",
            NotificationLevel.BLOCKED: "#ff6600",
            NotificationLevel.COMPLETE: "#00ff00",
        }

        payload = {
            "attachments": [
                {
                    "color": colors.get(level, "#808080"),
                    "title": f"Beyond Ralph [{level.value.upper()}]",
                    "text": message,
                    "ts": datetime.now().timestamp(),
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("Slack notification failed: %s", e)
            return False


class DiscordProvider(NotificationProvider):
    """Discord webhook notifications."""

    def __init__(self, webhook_url: str):
        """Initialize Discord provider.

        Args:
            webhook_url: Discord webhook URL.
        """
        self.webhook_url = webhook_url

    def is_configured(self) -> bool:
        """Check if webhook URL is set."""
        return bool(self.webhook_url)

    async def send(self, message: str, level: NotificationLevel) -> bool:
        """Send notification via Discord webhook."""
        if not self.is_configured():
            return False

        # Color based on level (Discord uses decimal)
        colors = {
            NotificationLevel.INFO: 3066993,  # Green
            NotificationLevel.WARNING: 16776960,  # Yellow
            NotificationLevel.ERROR: 15158332,  # Red
            NotificationLevel.BLOCKED: 15105570,  # Orange
            NotificationLevel.COMPLETE: 3066993,  # Green
        }

        payload = {
            "embeds": [
                {
                    "title": f"Beyond Ralph [{level.value.upper()}]",
                    "description": message,
                    "color": colors.get(level, 8421504),
                    "timestamp": datetime.now().isoformat(),
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30.0,
                )
                return response.status_code in (200, 204)
        except Exception as e:
            logger.error("Discord notification failed: %s", e)
            return False


class EmailProvider(NotificationProvider):
    """Email notifications via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addr: str,
    ):
        """Initialize email provider.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            username: SMTP username.
            password: SMTP password.
            from_addr: Sender email address.
            to_addr: Recipient email address.
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addr = to_addr

    def is_configured(self) -> bool:
        """Check if all required fields are set."""
        return all([
            self.smtp_host,
            self.smtp_port,
            self.username,
            self.password,
            self.from_addr,
            self.to_addr,
        ])

    async def send(self, message: str, level: NotificationLevel) -> bool:
        """Send notification via email."""
        if not self.is_configured():
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = self.to_addr
            msg["Subject"] = f"Beyond Ralph [{level.value.upper()}]"

            body = f"""
Beyond Ralph Notification
=========================

Level: {level.value.upper()}
Time: {datetime.now().isoformat()}

Message:
{message}

--
Beyond Ralph - Autonomous Development System
"""
            msg.attach(MIMEText(body, "plain"))

            # Send via SMTP (run in thread to not block)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg)
            return True

        except Exception as e:
            logger.error("Email notification failed: %s", e)
            return False

    def _send_smtp(self, msg: MIMEMultipart) -> None:
        """Send message via SMTP (blocking)."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)


class OSNotificationProvider(NotificationProvider):
    """Native OS notifications."""

    def is_configured(self) -> bool:
        """OS notifications are always available."""
        return True

    async def send(self, message: str, level: NotificationLevel) -> bool:
        """Send native OS notification."""
        try:
            import subprocess
            import sys

            title = f"Beyond Ralph [{level.value.upper()}]"

            if sys.platform == "darwin":
                # macOS
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ], capture_output=True)
            elif sys.platform == "linux":
                # Linux with notify-send
                subprocess.run([
                    "notify-send", title, message
                ], capture_output=True)
            elif sys.platform == "win32":
                # Windows with PowerShell
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Beyond Ralph").Show($toast)
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

            return True
        except Exception as e:
            logger.error("OS notification failed: %s", e)
            return False


class NotificationManager:
    """Manages notification channels and delivery."""

    def __init__(self):
        """Initialize notification manager."""
        self._providers: dict[NotificationChannel, NotificationProvider] = {}
        self._enabled_channels: set[NotificationChannel] = set()

    def configure_channel(
        self,
        channel: NotificationChannel,
        config: dict[str, Any],
    ) -> bool:
        """Configure a notification channel.

        Args:
            channel: The channel to configure.
            config: Channel-specific configuration.

        Returns:
            True if configuration succeeded.
        """
        try:
            if channel == NotificationChannel.SLACK:
                provider = SlackProvider(
                    webhook_url=config.get("webhook_url", ""),
                )
            elif channel == NotificationChannel.DISCORD:
                provider = DiscordProvider(
                    webhook_url=config.get("webhook_url", ""),
                )
            elif channel == NotificationChannel.EMAIL:
                provider = EmailProvider(
                    smtp_host=config.get("smtp_host", ""),
                    smtp_port=int(config.get("smtp_port", 587)),
                    username=config.get("username", ""),
                    password=config.get("password", ""),
                    from_addr=config.get("from_addr", ""),
                    to_addr=config.get("to_addr", ""),
                )
            elif channel == NotificationChannel.OS:
                provider = OSNotificationProvider()
            else:
                logger.warning("Unknown notification channel: %s", channel)
                return False

            if provider.is_configured():
                self._providers[channel] = provider
                self._enabled_channels.add(channel)
                return True
            else:
                logger.warning("Channel %s not properly configured", channel)
                return False

        except Exception as e:
            logger.error("Failed to configure channel %s: %s", channel, e)
            return False

    def disable_channel(self, channel: NotificationChannel) -> None:
        """Disable a notification channel.

        Args:
            channel: The channel to disable.
        """
        self._enabled_channels.discard(channel)

    def enable_channel(self, channel: NotificationChannel) -> bool:
        """Enable a notification channel.

        Args:
            channel: The channel to enable.

        Returns:
            True if the channel was configured and enabled.
        """
        if channel in self._providers:
            self._enabled_channels.add(channel)
            return True
        return False

    async def notify(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        channel: NotificationChannel | None = None,
    ) -> dict[NotificationChannel, bool]:
        """Send notification to configured channels.

        Args:
            message: The notification message.
            level: Severity level.
            channel: Specific channel to use, or None for all enabled.

        Returns:
            Dict mapping channels to success status.
        """
        results: dict[NotificationChannel, bool] = {}

        if channel is not None:
            # Send to specific channel
            if channel in self._providers and channel in self._enabled_channels:
                results[channel] = await self._providers[channel].send(message, level)
        else:
            # Send to all enabled channels
            for ch in self._enabled_channels:
                if ch in self._providers:
                    results[ch] = await self._providers[ch].send(message, level)

        return results

    async def notify_blocked(self, reason: str) -> dict[NotificationChannel, bool]:
        """Send a BLOCKED notification (needs user input).

        Args:
            reason: Why the system is blocked.

        Returns:
            Dict mapping channels to success status.
        """
        message = f"⚠️ BLOCKED: {reason}\n\nBeyond Ralph requires your input to continue."
        return await self.notify(message, NotificationLevel.BLOCKED)

    async def notify_error(self, error: str) -> dict[NotificationChannel, bool]:
        """Send an ERROR notification.

        Args:
            error: The error description.

        Returns:
            Dict mapping channels to success status.
        """
        message = f"❌ ERROR: {error}\n\nBeyond Ralph encountered an error."
        return await self.notify(message, NotificationLevel.ERROR)

    async def notify_complete(self, summary: str) -> dict[NotificationChannel, bool]:
        """Send a COMPLETE notification.

        Args:
            summary: Completion summary.

        Returns:
            Dict mapping channels to success status.
        """
        message = f"✅ COMPLETE: {summary}\n\nBeyond Ralph has finished the project."
        return await self.notify(message, NotificationLevel.COMPLETE)

    async def notify_quota_pause(self) -> dict[NotificationChannel, bool]:
        """Send notification about quota pause.

        Returns:
            Dict mapping channels to success status.
        """
        message = "⏸️ PAUSED: Quota limit reached (85%+).\n\nBeyond Ralph will resume automatically when quota resets."
        return await self.notify(message, NotificationLevel.WARNING)

    def get_enabled_channels(self) -> list[NotificationChannel]:
        """Get list of enabled channels.

        Returns:
            List of enabled NotificationChannel values.
        """
        return list(self._enabled_channels)

    def is_any_configured(self) -> bool:
        """Check if any notification channel is configured.

        Returns:
            True if at least one channel is configured.
        """
        return len(self._enabled_channels) > 0


# Singleton instance
_notification_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    """Get the notification manager singleton.

    Returns:
        The NotificationManager instance.
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


def configure_from_env() -> NotificationManager:
    """Configure notification manager from environment variables.

    Environment variables:
        BEYOND_RALPH_SLACK_WEBHOOK: Slack webhook URL
        BEYOND_RALPH_DISCORD_WEBHOOK: Discord webhook URL
        BEYOND_RALPH_SMTP_HOST: SMTP server host
        BEYOND_RALPH_SMTP_PORT: SMTP server port
        BEYOND_RALPH_SMTP_USER: SMTP username
        BEYOND_RALPH_SMTP_PASS: SMTP password
        BEYOND_RALPH_EMAIL_FROM: Sender email
        BEYOND_RALPH_EMAIL_TO: Recipient email

    Returns:
        Configured NotificationManager.
    """
    manager = get_notification_manager()

    # Slack
    slack_webhook = os.environ.get("BEYOND_RALPH_SLACK_WEBHOOK")
    if slack_webhook:
        manager.configure_channel(
            NotificationChannel.SLACK,
            {"webhook_url": slack_webhook},
        )

    # Discord
    discord_webhook = os.environ.get("BEYOND_RALPH_DISCORD_WEBHOOK")
    if discord_webhook:
        manager.configure_channel(
            NotificationChannel.DISCORD,
            {"webhook_url": discord_webhook},
        )

    # Email
    smtp_host = os.environ.get("BEYOND_RALPH_SMTP_HOST")
    if smtp_host:
        manager.configure_channel(
            NotificationChannel.EMAIL,
            {
                "smtp_host": smtp_host,
                "smtp_port": os.environ.get("BEYOND_RALPH_SMTP_PORT", "587"),
                "username": os.environ.get("BEYOND_RALPH_SMTP_USER", ""),
                "password": os.environ.get("BEYOND_RALPH_SMTP_PASS", ""),
                "from_addr": os.environ.get("BEYOND_RALPH_EMAIL_FROM", ""),
                "to_addr": os.environ.get("BEYOND_RALPH_EMAIL_TO", ""),
            },
        )

    # OS notifications (always available)
    manager.configure_channel(NotificationChannel.OS, {})

    return manager
