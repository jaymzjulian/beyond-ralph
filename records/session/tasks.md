# Session Module Tasks

## Overview

The session module provides Claude CLI session spawning and management, including UUID generation, lock files, and output streaming.

**Dependencies**: utils, quota
**Required By**: orchestrator
**Location**: `src/beyond_ralph/core/session_manager.py`
**Tests**: `tests/unit/test_session_manager.py`
**Status**: COMPLETE (implementation & mock tests)

---

## Task: Implement SessionInfo Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Define the SessionInfo dataclass for tracking session state.

**Acceptance Criteria**:
1. `uuid`: Unique identifier for the session
2. `status`: Current status (PENDING, RUNNING, COMPLETE, FAILED)
3. `start_time`: Timestamp when session started
4. `end_time`: Timestamp when session completed
5. `task`: The task description given to the session
6. `result`: The final result from the session
7. `output_lines`: List of streamed output lines

**Tests**: tests/unit/test_session_manager.py::TestSessionInfo
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/session-info/

---

## Task: Implement Session Spawning with pexpect

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Spawn new Claude CLI sessions using pexpect for interactive control.

**Acceptance Criteria**:
1. `spawn_cli(task)` creates new Claude CLI process
2. Use `--dangerously-skip-permissions` by default
3. Support `safemode` config to require permissions
4. Generate UUID for tracking
5. Return SessionInfo with UUID
6. Handle spawn failures gracefully

**Tests**: tests/unit/test_session_manager.py::TestSessionSpawning
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/session-spawning/

---

## Task: Implement Lock File Mechanism

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Prevent duplicate access to same session UUID.

**Acceptance Criteria**:
1. Create lock file before spawning
2. Check for existing lock before spawn
3. Lock contains PID of owning process
4. Clean up lock on normal exit
5. Handle stale locks (check if PID alive)
6. 5-minute timeout for force unlock

**Tests**: tests/unit/test_session_manager.py::TestLockFile
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/lock-file/

---

## Task: Implement Result Extraction

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Extract the final result message from session output.

**Acceptance Criteria**:
1. Wait for session to complete
2. Parse output for final result
3. Distinguish result from work output
4. Handle timeout gracefully
5. Support partial results on timeout
6. Return result in SessionInfo

**Tests**: tests/unit/test_session_manager.py::TestResultExtraction
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/result-extraction/

---

## Task: Implement Follow-up (--continue)

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Send follow-up requests to existing sessions.

**Acceptance Criteria**:
1. `continue_session(uuid, message)` sends follow-up
2. Use `--continue` flag with session UUID
3. Verify session still active before continue
4. Wait for and extract response
5. Handle "session not found" errors
6. Support multiple sequential follow-ups

**Tests**: tests/unit/test_session_manager.py::TestFollowUp
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/follow-up/

---

## Task: Implement Output Streaming

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Stream session output with [AGENT:uuid] prefix formatting.

**Acceptance Criteria**:
1. Real-time output streaming to callback
2. Prefix each line with `[AGENT:{uuid}]`
3. Support output buffer for replay
4. Handle binary output gracefully
5. Parse ANSI codes for clean output
6. SessionOutput dataclass for formatted output

**Tests**: tests/unit/test_session_manager.py::TestOutputStreaming
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/session/evidence/output-streaming/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| SessionInfo Dataclass | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Session Spawning | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Lock File Mechanism | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Result Extraction | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Follow-up (--continue) | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Output Streaming | [x] | [x] | [x] | [x] | [ ] | [ ] |

**Overall Progress**: 6/6 implemented, 6/6 mock tested, 6/6 integration tested, 0/6 live tested, 0/6 spec compliant
