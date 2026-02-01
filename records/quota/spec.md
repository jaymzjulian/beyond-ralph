# Module 6: Quota Management - Specification

**Module**: quota
**Location**: `src/beyond_ralph/core/quota_manager.py`
**Dependencies**: None (foundational)

## Purpose

Monitor Claude usage quotas and pause operations when nearing limits.

## Requirements

### R1: Quota Detection
- Check `claude /usage` command (or similar)
- Parse session percentage
- Parse weekly percentage
- Detect subscription tier at runtime

### R2: Threshold Enforcement
- PAUSE at 85% (either session OR weekly)
- Do NOT stop, just PAUSE
- Allow manual resume override

### R3: Caching
- Cache quota status in file (everyone can read)
- 5-minute cache during normal operation
- 10-minute check interval when paused

### R4: Pre-Interaction Check
- Check quota BEFORE each agent spawn
- Block spawn if over threshold
- Notify user of pause

## Interface

```python
@dataclass
class QuotaStatus:
    session_percent: float
    weekly_percent: float
    is_limited: bool
    checked_at: datetime

class QuotaManager:
    async def check(self, force_refresh: bool = False) -> QuotaStatus
    async def wait_for_reset(self) -> None
    def is_limited(self) -> bool
    def get_cache_path(self) -> Path
```

## Testing Requirements

- Mock claude /usage output
- Test threshold detection
- Test caching behavior
- Test pause/resume cycle
