# Core Module Tasks

## Overview

The core module provides fundamental infrastructure: session management, quota monitoring, knowledge base, and records system.

**Dependencies**: utils
**Required By**: agents, orchestrator, skills, hooks

---

## Task: Implement Session Manager

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Create the session manager that spawns and controls Claude Code sessions via CLI.

**Acceptance Criteria**:
1. `spawn_cli()` creates new Claude Code session and returns UUID
2. `--dangerously-skip-permissions` flag used by default (configurable via `safemode`)
3. Session output captured and formatted with `[AGENT:uuid]` prefix
4. `send()` method sends follow-up messages using `--continue` flag
5. Lock file prevents duplicate access to same session
6. Result extraction identifies final human-readable message
7. Cleanup releases locks and terminates session cleanly
8. pexpect handles interactive CLI sessions

**Tests**: tests/unit/test_session_manager.py (38 tests, 47% coverage)
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/session-manager/

---

## Task: Implement Quota Manager

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Monitor Claude usage quotas and pause operations when nearing limits.

**Acceptance Criteria**:
1. Parse `claude /usage` command output via pexpect
2. Extract session percentage (0-100)
3. Extract weekly percentage (0-100)
4. Cache status in file (5min TTL normal, 10min when limited)
5. Return `is_limited=True` when either >= 85%
6. `is_unknown=True` blocks operations (never fake results)
7. `br-quota` CLI shows current quota status
8. PAUSE behavior (don't terminate, just wait)
9. 10-minute retry interval when paused

**Tests**: tests/unit/test_quota_manager.py (11 tests)
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/quota-manager/

---

## Task: Implement Knowledge Base

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2026-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Shared knowledge base for agent information sharing (beyondralph_knowledge/).

**Acceptance Criteria**:
1. `write()` creates knowledge entry with YAML frontmatter
2. Entries include source session UUID for attribution
3. `read()` retrieves entry by topic name
4. `search()` finds entries matching query
5. `list_recent(hours=24)` returns recent entries for compaction recovery
6. Entries support structured format (summary, details, related topics)
7. Follow-up questions field enables cross-session queries
8. Knowledge checked BEFORE asking orchestrator

**Tests**: tests/unit/test_knowledge.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/knowledge-base/

---

## Task: Implement Records System

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Per-module task tracking with 6-checkbox system.

**Acceptance Criteria**:
1. RecordsManager supports CRUD operations on tasks
2. Each task has exactly 6 checkboxes:
   - Planned
   - Implemented
   - Mock tested
   - Integration tested
   - Live tested
   - Spec compliant
3. `update_checkbox()` marks/unmarks individual checkboxes
4. Testing agent CAN remove checkboxes on failure
5. SpecComplianceAgent CAN remove "Implemented" checkbox
6. Evidence path tracked per task
7. Implementation/Validation agent UUIDs recorded
8. `get_status_summary()` returns "X/6" format

**Tests**: tests/unit/test_records.py (10 tests)
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/records-system/

---

## Task: Implement Principles Module

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Core integrity rules enforced across all agents.

**Acceptance Criteria**:
1. CORE_PRINCIPLES constant defines "never fake results" rules
2. AGENT_PRINCIPLES_PROMPT injected into all agent prompts
3. AGENT_RUNTIME_BEHAVIORS defines git, TODO, planning behaviors
4. RESOURCE_CHECK_PROMPT for interview phase resource verification
5. All child agents receive principles in their system prompt
6. Honest error handling enforced (no silent exceptions)
7. Explicit fallbacks required (all logged and marked)
8. Verifiable success (claims backed by evidence)

**Tests**: tests/unit/test_principles.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/principles/

---

## Task: Implement API Documentation Ingester

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Ingest API documentation as part of development.

**Acceptance Criteria**:
1. APIDocIngester class parses OpenAPI/Swagger specs
2. Extract endpoints, methods, parameters, responses
3. Generate mock server configuration from spec
4. Store parsed documentation in knowledge base
5. Support URL and file-based spec loading
6. Handle JSON and YAML formats
7. Generate type hints from schemas

**Tests**: tests/unit/test_api_docs.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/api-docs/

---

## Task: Implement Dynamic Plan Manager

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Inter-module requirement tracking (modules can add requirements to other modules).

**Acceptance Criteria**:
1. `add_requirement()` adds technical requirement from one module to another
2. Requirements are technical only (no user input needed)
3. PROJECT_PLAN.md auto-updated with new requirements
4. Orchestrator can `get_pending_requirements()`
5. `get_work_for_module()` returns scheduled work
6. `mark_failed()` records when module fails to deliver
7. `report_discrepancy()` tracks promised vs delivered
8. Discrepancy severity levels (CRITICAL, HIGH, MEDIUM, LOW)

**Tests**: tests/unit/test_dynamic_plan.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/dynamic-plan/

---

## Task: Implement Review Loop Manager

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Code review fix-loop (coder MUST action ALL review items).

**Acceptance Criteria**:
1. ReviewItem dataclass tracks individual findings
2. ReviewCycle dataclass tracks review iteration
3. `generate_fix_prompt()` creates prompt for coder agent
4. Coder agent MUST fix ALL items (non-negotiable)
5. `verify_fix()` confirms item was fixed
6. `is_cycle_complete()` checks if all must-fix items resolved
7. `approve_cycle()` marks cycle as approved
8. Loop continues until 0 must-fix items

**Tests**: tests/unit/test_review_loop.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/review-loop/

---

## Task: Implement User Interaction Manager

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Route AskUserQuestion from subagents to main session.

**Acceptance Criteria**:
1. `request_question()` routes AskUserQuestion from subagent
2. `submit_response()` delivers user response to subagent
3. `request_interrupt()` handles user-initiated interrupt
4. Progress updates streamed via `send_progress()`
5. ProgressUpdate dataclass for structured updates
6. UserInteraction dataclass for question/response pairs
7. Support multiple concurrent questions
8. Timeout handling for unanswered questions

**Tests**: tests/unit/test_user_interaction.py
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/user-interaction/

---

## Task: Implement Notification System

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2026-02-03
- [x] Live tested - 2026-02-03 (review loop in use)
- [x] Spec compliant - 2026-02-03

**Description**: Multi-channel notifications for autonomous operation.

**Acceptance Criteria**:
1. NotificationManager class coordinates all providers
2. SlackProvider sends Slack webhook notifications
3. DiscordProvider sends Discord webhook notifications
4. EmailProvider sends email notifications
5. Event-based notifications (phase complete, quota warning, error)
6. Configurable notification levels (INFO, WARNING, ERROR)
7. Provider enable/disable per notification type
8. Retry logic for failed notifications

**Tests**: tests/unit/test_notifications.py (18 tests)
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/core/evidence/notifications/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| Session Manager | [x] | [x] | [x] | [x] | [x] | [x] |
| Quota Manager | [x] | [x] | [x] | [x] | [x] | [x] |
| Knowledge Base | [x] | [x] | [x] | [x] | [x] | [x] |
| Records System | [x] | [x] | [x] | [x] | [x] | [x] |
| Principles Module | [x] | [x] | [x] | [x] | [x] | [x] |
| API Documentation Ingester | [x] | [x] | [x] | [x] | [x] | [x] |
| Dynamic Plan Manager | [x] | [x] | [x] | [x] | [x] | [x] |
| Review Loop Manager | [x] | [x] | [x] | [x] | [x] | [x] |
| User Interaction Manager | [x] | [x] | [x] | [x] | [x] | [x] |
| Notification System | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 10/10 implemented, 10/10 mock tested, 10/10 integration tested, 10/10 live tested, 10/10 spec compliant
