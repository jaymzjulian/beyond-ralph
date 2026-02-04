# Module 1.3: Quota Manager - Specification

> Quota Management: Detect and handle Claude usage quotas.

---

## Overview

The Quota Manager detects Claude usage quotas and manages PAUSE behavior when quotas are near limits. It is critical for autonomous operation without human intervention.

**Key Principle**: NEVER fake quota results. Unknown state blocks operations.

---

## Location

`src/beyond_ralph/core/quota_manager.py`

---

## Components

### Quota Manager Class

**Purpose**: Monitor and enforce quota limits.

**Interface**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import asyncio

@dataclass
class QuotaStatus:
    """Current quota status."""
    session_percent: int
    weekly_percent: int
    is_limited: bool
    is_unknown: bool  # CRITICAL: blocks operations when True
    last_checked: datetime
    reset_time: Optional[datetime]

class QuotaManager:
    """Manages quota checking and pause behavior."""

    THRESHOLD: int = 85  # Pause at 85%
    CHECK_INTERVAL: int = 600  # 10 minutes in seconds

    def __init__(self, cache_file: str = ".beyond_ralph_quota") -> None:
        """Initialize quota manager.

        Args:
            cache_file: Path to quota cache file.
        """
        self.cache_file = cache_file
        self._cached_status: Optional[QuotaStatus] = None

    def check(self, force_refresh: bool = False) -> QuotaStatus:
        """Check current quota status.

        Args:
            force_refresh: If True, bypass cache.

        Returns:
            QuotaStatus with session and weekly percentages.

        Flow:
            1. Check cache (if not force_refresh)
            2. If cache valid (< 5 min old), return cached
            3. Run 'claude /usage' via pexpect
            4. Parse output for percentages
            5. Update cache
            6. Return status

        IMPORTANT:
            If parsing fails, returns is_unknown=True.
            NEVER fake results.
        """

    def is_limited(self) -> bool:
        """Check if quota is at or above threshold.

        Returns True if either:
            - session_percent >= 85
            - weekly_percent >= 85
            - is_unknown is True (safety)
        """

    async def wait_for_reset(self) -> None:
        """Wait until quota resets.

        Checks every 10 minutes until quota is below threshold.

        Flow:
            1. Check quota
            2. If limited, sleep 10 minutes
            3. Repeat until not limited
        """

    def pre_spawn_check(self) -> None:
        """Check quota before spawning agent.

        Raises:
            QuotaLimitError: If quota >= 85%.
            QuotaUnknownError: If quota cannot be determined.
        """

    def _read_cache(self) -> Optional[QuotaStatus]:
        """Read cached quota status from file."""

    def _write_cache(self, status: QuotaStatus) -> None:
        """Write quota status to cache file."""

    def _run_usage_check(self) -> tuple[int, int]:
        """Run claude /usage and parse output.

        Uses pexpect to:
            1. Start 'claude' process
            2. Send '/usage' command
            3. Read output
            4. Send escape and '/quit' to exit

        Returns:
            Tuple of (session_percent, weekly_percent).

        Raises:
            ValueError: If output cannot be parsed.
        """
```

---

## Quota States

| State | Session % | Weekly % | Action |
|-------|-----------|----------|--------|
| GREEN | <85 | <85 | Normal operation |
| YELLOW | 85-95 | <85 | Slow down, essential only |
| RED | >=95 | ANY | PAUSE, wait for reset |
| RED | ANY | >=85 | PAUSE, wait for reset |
| UNKNOWN | ? | ? | PAUSE, try again later |

---

## Cache File Format

`.beyond_ralph_quota`:
```json
{
  "session_percent": 35,
  "weekly_percent": 26,
  "is_limited": false,
  "is_unknown": false,
  "last_checked": "2026-02-02T14:30:00",
  "reset_time": null
}
```

---

## Usage Parsing

Expected output from `claude /usage`:
```
Session: 35% (tokens: 12,345/35,000)
Weekly: 26% (tokens: 234,567/900,000)
```

Parsing regex:
```python
import re

SESSION_PATTERN = r"Session:\s*(\d+)%"
WEEKLY_PATTERN = r"Weekly:\s*(\d+)%"

def parse_usage_output(output: str) -> tuple[int, int]:
    session_match = re.search(SESSION_PATTERN, output)
    weekly_match = re.search(WEEKLY_PATTERN, output)

    if not session_match or not weekly_match:
        raise ValueError("Could not parse quota output")

    return int(session_match.group(1)), int(weekly_match.group(1))
```

---

## Integration with Orchestrator

```python
# Before spawning any agent:
quota_manager = QuotaManager()

try:
    quota_manager.pre_spawn_check()
except QuotaLimitError:
    # Pause and wait
    await quota_manager.wait_for_reset()
except QuotaUnknownError:
    # Cannot proceed - unknown state
    raise
```

---

## Never Fake Results

**CRITICAL**: This is a core principle.

If we cannot determine quota:
- DO NOT assume it's OK
- DO NOT proceed anyway
- DO block operations
- DO report the error

```python
if status.is_unknown:
    raise QuotaUnknownError(
        "Cannot determine quota status. "
        "Blocking operations to prevent overage."
    )
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 12 (Utils) | Logging, file operations |

---

## Error Handling

```python
class QuotaError(BeyondRalphError):
    """Quota-related errors."""

class QuotaLimitError(QuotaError):
    """At or above quota limit."""

class QuotaUnknownError(QuotaError):
    """Cannot determine quota status."""

class QuotaParseError(QuotaError):
    """Failed to parse quota output."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | Parsing, cache management |
| Integration tests | Quota checking flow |
| Live tests | Real Claude /usage |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [x] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
