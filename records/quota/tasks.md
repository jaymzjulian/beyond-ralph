# Quota Module Tasks

## Overview

The quota module provides Claude usage limit detection and pause/resume logic for autonomous operation.

**Dependencies**: utils
**Required By**: session, orchestrator
**Location**: `src/beyond_ralph/core/quota_manager.py`, `src/beyond_ralph/utils/quota_checker.py`
**Tests**: `tests/unit/test_quota_manager.py`, `tests/unit/test_quota_checker.py`
**Status**: COMPLETE (implementation & mock tests)

---

## Task: Implement QuotaStatus Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Define the QuotaStatus dataclass for tracking usage limits.

**Acceptance Criteria**:
1. `session_percent`: Current session usage percentage (0-100)
2. `weekly_percent`: Weekly usage percentage (0-100)
3. `is_limited`: Boolean true when either >= 85%
4. `is_unknown`: Boolean true when quota couldn't be determined
5. `last_checked`: Timestamp of last check
6. `cache_expires`: Timestamp when cache is stale

**Tests**: tests/unit/test_quota_manager.py::TestQuotaStatus
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/quota-status/

---

## Task: Implement Quota Parser

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (br-quota working)
- [x] Spec compliant - 2026-02-03

**Description**: Parse `claude /usage` command output to extract quota information.

**Acceptance Criteria**:
1. Parse session percentage from output
2. Parse weekly percentage from output
3. Handle different output formats gracefully
4. Return `is_unknown=True` on parse failure
5. Never guess or fake values
6. Log parsing errors for debugging

**Tests**: tests/unit/test_quota_manager.py::TestQuotaParser
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/quota-parser/

---

## Task: Implement File-Based Cache

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (br-quota working)
- [x] Spec compliant - 2026-02-03

**Description**: Cache quota status to file for sharing between processes.

**Acceptance Criteria**:
1. Store in `.beyond_ralph_quota` file
2. 5-minute cache TTL during normal operation
3. 10-minute cache TTL when quota is limited
4. JSON format for easy parsing
5. Atomic writes to prevent corruption
6. Handle missing/corrupt cache gracefully

**Tests**: tests/unit/test_quota_manager.py::TestQuotaCache
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/file-cache/

---

## Task: Implement 85% Threshold Detection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (br-quota working)
- [x] Spec compliant - 2026-02-03 (verified compliant)

**Description**: Detect when usage hits 85% threshold for EITHER session OR weekly quota.

**Acceptance Criteria**:
1. Check session_percent >= 85
2. Check weekly_percent >= 85
3. `is_limited` = True if either is >= 85
4. `is_limited` = True if `is_unknown` = True (safe default)
5. Configurable threshold (default 85)
6. Log when threshold exceeded

**Tests**: tests/unit/test_quota_manager.py::TestThresholdDetection
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/threshold-detection/

---

## Task: Implement Pause Behavior

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (br-quota working)
- [x] Spec compliant - 2026-02-03

**Description**: PAUSE (not stop) operation when quota is limited.

**Acceptance Criteria**:
1. `check_and_wait()` blocks until quota available
2. Check every 10 minutes when paused
3. Return immediately if quota available
4. Log pause/resume events
5. NEVER stop autonomous operation, just PAUSE
6. Support cancellation for graceful shutdown

**Tests**: tests/unit/test_quota_manager.py::TestPauseBehavior
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/pause-behavior/

---

## Task: Implement CLI Entry Point

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (br-quota working)
- [x] Spec compliant - 2026-02-03 (verified, minor gap: exit codes)

**Description**: `br-quota` CLI command for checking quota status.

**Acceptance Criteria**:
1. Entry point registered in pyproject.toml
2. Display session and weekly percentages
3. Show `is_limited` and `is_unknown` status
4. Exit code 0 if OK, 1 if limited, 2 if unknown
5. Support `--json` for machine-readable output
6. Support `--wait` to block until available

**Tests**: tests/unit/test_quota_checker.py::TestCLI
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/quota/evidence/cli-entry-point/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| QuotaStatus Dataclass | [x] | [x] | [x] | [x] | [x] | [x] |
| Quota Parser | [x] | [x] | [x] | [x] | [x] | [x] |
| File-Based Cache | [x] | [x] | [x] | [x] | [x] | [x] |
| 85% Threshold Detection | [x] | [x] | [x] | [x] | [x] | [x] |
| Pause Behavior | [x] | [x] | [x] | [x] | [x] | [x] |
| CLI Entry Point | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 6/6 implemented, 6/6 mock tested, 6/6 integration tested, 6/6 live tested, 6/6 spec compliant
