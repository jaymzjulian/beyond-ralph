# Module 9: Notifications - Specification

> User Notifications: Alert users when blocked or needing input via multiple channels.

---

## Overview

The Notifications module sends alerts to users when Beyond Ralph is blocked or needs input. Per interview decision, notifications are sent ONLY when blocked - not for progress updates. Multiple channels are supported including Slack, Discord, Email, and webhooks.

**Key Principle**: Notify ONLY when stuck. Don't spam with progress updates.

---

## Components

### 9.1 Notification Manager (`notifications.py`)

**Location**: `src/beyond_ralph/core/notifications.py`

---

## Notification Triggers

| Trigger | Description | Priority |
|---------|-------------|----------|
| **Blocked** | Cannot proceed without user action | HIGH |
| **Needs Input** | AskUserQuestion waiting for response | HIGH |
| **Error** | Critical error that may need attention | HIGH |
| **Complete** | Project finished (optional notification) | LOW |

**NOT triggered for**:
- Progress updates
- Phase transitions
- Agent spawning
- Routine operations

---

## Supported Channels

| Channel | Method | Configuration |
|---------|--------|---------------|
| **Slack** | Webhook | `SLACK_WEBHOOK_URL` |
| **Discord** | Webhook | `DISCORD_WEBHOOK_URL` |
| **Email** | SMTP | `EMAIL_SMTP_*` settings |
| **WhatsApp** | whatsmeow | `WHATSAPP_*` settings |
| **OS Notifications** | Native | Auto-detect |
| **Custom Webhooks** | HTTP POST | `CUSTOM_WEBHOOKS` list |

---

## Interfaces

### NotificationManager

```python
class NotificationManager:
    """Multi-channel notification manager."""

    def __init__(self, config: NotificationConfig):
        """Initialize notification manager.

        Args:
            config: Notification configuration.
        """

    async def notify_blocked(
        self,
        reason: str,
        module: str,
        context: Optional[dict] = None
    ) -> None:
        """Notify user that Beyond Ralph is blocked.

        Args:
            reason: Why we're blocked.
            module: Which module is blocked.
            context: Additional context.

        Sends to all configured channels.
        """

    async def notify_needs_input(
        self,
        question: str,
        options: Optional[list[str]] = None
    ) -> None:
        """Notify user that input is needed.

        Args:
            question: The question being asked.
            options: Available options (if any).
        """

    async def notify_error(
        self,
        error: str,
        context: str,
        traceback: Optional[str] = None
    ) -> None:
        """Notify user of critical error.

        Args:
            error: Error message.
            context: Where the error occurred.
            traceback: Optional stack trace.
        """

    async def notify_complete(
        self,
        summary: str,
        stats: Optional[dict] = None
    ) -> None:
        """Notify user that project is complete.

        Args:
            summary: Completion summary.
            stats: Optional statistics (tasks, duration, etc.)
        """

    def _format_message(
        self,
        title: str,
        body: str,
        channel: str
    ) -> str:
        """Format message for specific channel.

        Different channels have different formatting:
            - Slack: Use blocks and mrkdwn
            - Discord: Use embeds
            - Email: HTML formatting
            - Webhooks: JSON payload
        """

@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None
    email_smtp: Optional[EmailConfig] = None
    whatsapp_config: Optional[WhatsAppConfig] = None
    custom_webhooks: list[str] = field(default_factory=list)
    enable_os_notifications: bool = True

@dataclass
class EmailConfig:
    """SMTP email configuration."""
    host: str
    port: int
    username: str
    password: str  # From environment variable
    from_address: str
    to_addresses: list[str]
    use_tls: bool = True

@dataclass
class WhatsAppConfig:
    """WhatsApp configuration (via whatsmeow)."""
    phone_number: str
    session_path: str
```

### Channel Implementations

```python
class SlackNotifier:
    """Slack webhook notifier."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, title: str, body: str, priority: str) -> bool:
        """Send Slack notification.

        Uses Slack Block Kit for formatting.
        """

class DiscordNotifier:
    """Discord webhook notifier."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, title: str, body: str, priority: str) -> bool:
        """Send Discord notification.

        Uses Discord embeds for formatting.
        """

class EmailNotifier:
    """Email SMTP notifier."""

    def __init__(self, config: EmailConfig):
        self.config = config

    async def send(self, title: str, body: str, priority: str) -> bool:
        """Send email notification.

        Uses HTML formatting.
        """

class OSNotifier:
    """Native OS notification."""

    async def send(self, title: str, body: str, priority: str) -> bool:
        """Send OS notification.

        Uses:
            - notify-send on Linux
            - osascript on macOS
            - toast on Windows
        """

class WebhookNotifier:
    """Generic webhook notifier."""

    def __init__(self, url: str):
        self.url = url

    async def send(self, title: str, body: str, priority: str) -> bool:
        """Send webhook notification.

        POST JSON payload to URL.
        """
```

---

## Message Formats

### Slack

```python
slack_payload = {
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 Beyond Ralph - Blocked"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:* {reason}\n*Module:* {module}"
            }
        }
    ]
}
```

### Discord

```python
discord_payload = {
    "embeds": [{
        "title": "🚨 Beyond Ralph - Blocked",
        "description": f"**Reason:** {reason}\n**Module:** {module}",
        "color": 15158332  # Red
    }]
}
```

### Email

```html
<html>
<body>
  <h1>🚨 Beyond Ralph - Blocked</h1>
  <p><strong>Reason:</strong> {reason}</p>
  <p><strong>Module:</strong> {module}</p>
</body>
</html>
```

### Webhook (Generic)

```json
{
  "event": "blocked",
  "timestamp": "2024-02-01T10:30:00Z",
  "project": "my-project",
  "data": {
    "reason": "Cannot find API endpoint",
    "module": "testing"
  }
}
```

---

## Configuration

```yaml
# beyond-ralph.yaml
notifications:
  slack_webhook: ${SLACK_WEBHOOK_URL}
  discord_webhook: ${DISCORD_WEBHOOK_URL}

  email:
    host: smtp.gmail.com
    port: 587
    username: ${EMAIL_USER}
    password: ${EMAIL_PASSWORD}
    from_address: beyond-ralph@example.com
    to_addresses:
      - user@example.com
    use_tls: true

  custom_webhooks:
    - https://api.example.com/webhooks/beyond-ralph

  enable_os_notifications: true
```

---

## Usage Example

```python
# In orchestrator when blocked
notification_manager = NotificationManager(config.notifications)

# Notify all channels
await notification_manager.notify_blocked(
    reason="Cannot find API endpoint /users",
    module="testing",
    context={"endpoint": "/users", "expected": "200 OK"}
)
```

---

## Dependencies

None - this is a leaf module with no external dependencies (uses httpx which is already a project dependency).

---

## Error Handling

```python
class NotificationError(BeyondRalphError):
    """Notification-specific errors."""

class ChannelConfigError(NotificationError):
    """Channel not properly configured."""

class DeliveryFailedError(NotificationError):
    """Failed to deliver notification."""
```

**Note**: Notification failures should NOT block Beyond Ralph operation. Log and continue.

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Message formatting, config parsing |
| Integration tests | Webhook delivery (mocked endpoints) |
| Mock tests | Mocked HTTP calls |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested (99% coverage)
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
