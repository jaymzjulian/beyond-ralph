# User Interaction Module Tasks

## Overview

The user-interaction module routes AskUserQuestion from subagents to the main Claude Code session.

**Dependencies**: orchestrator
**Required By**: skills
**Location**: `src/beyond_ralph/core/user_interaction.py`
**Tests**: `tests/unit/test_user_interaction.py` (15 tests)
**LOC**: 544

---

## Task: Implement UserInteractionManager Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Main class for managing user interactions from subagents.

**Acceptance Criteria**:
1. `UserInteractionManager` class
2. Queue incoming questions from subagents
3. Route to main Claude Code session
4. Track pending questions
5. Support multiple concurrent questions
6. Timeout handling for unanswered questions

**Tests**: tests/unit/test_user_interaction.py::TestUserInteractionManager
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/interaction-manager/

---

## Task: Implement request_question Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Route AskUserQuestion from subagent to main session.

**Acceptance Criteria**:
1. `request_question(agent_uuid, question, options)` routes question
2. Format question for AskUserQuestion tool
3. Track which agent asked
4. Queue if main session busy
5. Return question ID for response matching

**Tests**: tests/unit/test_user_interaction.py::TestRequestQuestion
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/request-question/

---

## Task: Implement submit_response Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Deliver user response to waiting subagent.

**Acceptance Criteria**:
1. `submit_response(question_id, response)` delivers response
2. Match response to waiting agent
3. Unblock waiting agent
4. Handle response timeout
5. Log response for evidence

**Tests**: tests/unit/test_user_interaction.py::TestSubmitResponse
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/submit-response/

---

## Task: Implement request_interrupt Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Handle user-initiated interrupts.

**Acceptance Criteria**:
1. `request_interrupt()` pauses subagent work
2. User can interrupt long-running operations
3. Save state before interrupting
4. Resume capability after interrupt
5. Notify affected subagents

**Tests**: tests/unit/test_user_interaction.py::TestRequestInterrupt
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/request-interrupt/

---

## Task: Implement send_progress Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Stream progress updates to main session.

**Acceptance Criteria**:
1. `send_progress(agent_uuid, message)` sends progress
2. Format with [AGENT:uuid] prefix
3. Real-time streaming to UI
4. Support rich formatting
5. Non-blocking (don't wait for ack)

**Tests**: tests/unit/test_user_interaction.py::TestSendProgress
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/send-progress/

---

## Task: Implement ProgressUpdate Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Dataclass for structured progress updates.

**Acceptance Criteria**:
1. `ProgressUpdate` dataclass with:
   - `agent_uuid`: Source agent
   - `message`: Progress message
   - `timestamp`: When sent
   - `progress_type`: INFO/STATUS/WARNING/ERROR
   - `metadata`: Optional extra data
2. Serialize for transmission
3. Format for display

**Tests**: tests/unit/test_user_interaction.py::TestProgressUpdate
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/progress-update/

---

## Task: Implement UserInteraction Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (AskUserQuestion working)
- [x] Spec compliant - 2026-02-03

**Description**: Dataclass for question/response pairs.

**Acceptance Criteria**:
1. `UserInteraction` dataclass with:
   - `question_id`: Unique identifier
   - `agent_uuid`: Asking agent
   - `question`: Question text
   - `options`: Available choices
   - `response`: User's answer
   - `asked_at`: Timestamp
   - `answered_at`: Timestamp
2. Track interaction lifecycle
3. Support evidence collection

**Tests**: tests/unit/test_user_interaction.py::TestUserInteraction
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/user-interaction/evidence/user-interaction/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| UserInteractionManager Class | [x] | [x] | [x] | [x] | [x] | [x] |
| request_question Method | [x] | [x] | [x] | [x] | [x] | [x] |
| submit_response Method | [x] | [x] | [x] | [x] | [x] | [x] |
| request_interrupt Method | [x] | [x] | [x] | [x] | [x] | [x] |
| send_progress Method | [x] | [x] | [x] | [x] | [x] | [x] |
| ProgressUpdate Dataclass | [x] | [x] | [x] | [x] | [x] | [x] |
| UserInteraction Dataclass | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 7/7 implemented, 7/7 mock tested, 7/7 integration tested, 7/7 live tested, 7/7 spec compliant
