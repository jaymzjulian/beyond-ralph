# Module 12: Notification System - Specification

**Module**: notifications
**Location**: `src/beyond_ralph/core/notifications.py`
**Dependencies**: None (foundational)

## Purpose

Remote notifications for unsupervised operation - alert user when blocked or when project completes.

## Requirements

### R1: Notification Channels
- Slack (via webhook)
- Discord (via webhook)
- Email (SMTP)
- WhatsApp (via whatsmeow - optional)
- OS notifications (native)

### R2: Notification Triggers
- ONLY when blocked/needs user input
- NOT for progress updates (avoid spam)
- Project completion
- Fatal errors
- Quota pauses

### R3: Configuration
- Credentials collected during interview phase
- Stored encrypted at rest
- Support multiple channels simultaneously

### R4: Webhook Support
- Outgoing webhooks for CI/CD integration
- POST to configured URLs on events
- Configurable payload format

## Interface

```python
class NotificationManager:
    async def notify(
        self,
        message: str,
        level: NotificationLevel,
        channel: str | None = None,
    ) -> None

    async def configure_channel(
        self,
        channel: str,
        credentials: dict,
    ) -> None

    async def send_webhook(
        self,
        url: str,
        payload: dict,
    ) -> None

    async def test_channel(self, channel: str) -> bool
```

## Notification Levels

```python
class NotificationLevel(Enum):
    INFO = "info"           # Project completion
    WARNING = "warning"     # Quota pause
    ERROR = "error"         # Fatal error
    BLOCKED = "blocked"     # Needs user input
```

## Testing Requirements

- Mock webhook endpoints
- Test each channel type
- Test message formatting
- Test credential encryption
