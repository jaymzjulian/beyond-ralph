# Orchestrator Module Tasks

## Overview

The orchestrator module provides the main phase coordination loop, implementing the 8-phase methodology with quota awareness and agent delegation.

**Dependencies**: session, quota, agents
**Required By**: skills, hooks
**Location**: `src/beyond_ralph/core/orchestrator.py`
**Tests**: `tests/unit/test_orchestrator.py`
**Status**: COMPLETE (implementation & mock tests)

---

## Task: Implement Orchestrator State Machine

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (Beyond Ralph self-hosting session)
- [x] Spec compliant - 2026-02-03 (verified by code-reviewer)

**Description**: Core state machine managing phase transitions.

**Acceptance Criteria**:
1. OrchestratorState enum (IDLE, RUNNING, PAUSED, COMPLETE, FAILED)
2. Current phase tracking (1-8)
3. Transition validation (no skipping phases)
4. State persistence for resume
5. Error state handling
6. State change callbacks

**Tests**: tests/unit/test_orchestrator.py::TestStateMachine
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/state-machine/

---

## Task: Implement start() Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (Beyond Ralph self-hosting session)
- [x] Spec compliant - 2026-02-03

**Description**: Start new orchestration from specification file.

**Acceptance Criteria**:
1. Accept spec file path
2. Initialize state to Phase 1
3. Check quota before starting
4. Create project folder structure
5. Initialize records
6. Begin phase execution loop

**Tests**: tests/unit/test_orchestrator.py::TestStart
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/start-method/

---

## Task: Implement resume() Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (/beyond-ralph-resume command working)
- [x] Spec compliant - 2026-02-03

**Description**: Resume paused or interrupted orchestration.

**Acceptance Criteria**:
1. Read persisted state
2. Restore current phase
3. Check quota before resuming
4. Re-read PROJECT_PLAN.md (compaction recovery)
5. Re-read recent knowledge entries
6. Continue from checkpoint

**Tests**: tests/unit/test_orchestrator.py::TestResume
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/resume-method/

---

## Task: Implement pause() Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Manual pause of orchestration.

**Acceptance Criteria**:
1. Set state to PAUSED
2. Persist current state
3. Complete current agent task first
4. Save checkpoint for resume
5. Clean up active resources
6. Return pause confirmation

**Tests**: tests/unit/test_orchestrator.py::TestPause
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/pause-method/

---

## Task: Implement Phase Transitions

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Manage transitions between phases 1-8.

**Acceptance Criteria**:
1. Phase 1 -> 2: After spec ingestion complete
2. Phase 2 -> 3: After interview complete (no more questions)
3. Phase 3 -> 4: After modular spec created
4. Phase 4 -> 5: After project plan created
5. Phase 5 -> 6 or back to 2: After uncertainty review
6. Phase 6 -> 7: After validation complete
7. Phase 7 -> 8: After implementation complete
8. Phase 8 -> COMPLETE or back to 7: After testing

**Tests**: tests/unit/test_orchestrator.py::TestPhaseTransitions
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/phase-transitions/

---

## Task: Implement Quota Check Integration

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Check quota before every agent interaction.

**Acceptance Criteria**:
1. Call quota_manager.check() before spawning
2. If `is_limited`, pause and wait
3. If `is_unknown`, pause (safe default)
4. Log quota status
5. Continue when quota available
6. Integrate with PAUSE state

**Tests**: tests/unit/test_orchestrator.py::TestQuotaIntegration
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/quota-integration/

---

## Task: Implement Agent Delegation

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Delegate work to specialized agents.

**Acceptance Criteria**:
1. Orchestrator ONLY orchestrates (minimal context)
2. Spawn appropriate agent for each phase
3. Pass task context to agent
4. Receive result from agent
5. Store agent knowledge contributions
6. Update records with agent work

**Tests**: tests/unit/test_orchestrator.py::TestAgentDelegation
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/agent-delegation/

---

## Task: Implement Compaction Recovery Protocol

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03
- [x] Spec compliant - 2026-02-03

**Description**: Recovery protocol after context compaction.

**Acceptance Criteria**:
1. Detect compaction events
2. IMMEDIATELY re-read PROJECT_PLAN.md
3. IMMEDIATELY re-read current module specs
4. IMMEDIATELY re-read task status
5. IMMEDIATELY check recent knowledge entries
6. Resume from last known good state

**Tests**: tests/unit/test_orchestrator.py::TestCompactionRecovery
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/orchestrator/evidence/compaction-recovery/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| Orchestrator State Machine | [x] | [x] | [x] | [x] | [x] | [x] |
| start() Method | [x] | [x] | [x] | [x] | [x] | [x] |
| resume() Method | [x] | [x] | [x] | [x] | [x] | [x] |
| pause() Method | [x] | [x] | [x] | [x] | [x] | [x] |
| Phase Transitions | [x] | [x] | [x] | [x] | [x] | [x] |
| Quota Check Integration | [x] | [x] | [x] | [x] | [x] | [x] |
| Agent Delegation | [x] | [x] | [x] | [x] | [x] | [x] |
| Compaction Recovery Protocol | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 8/8 implemented, 8/8 mock tested, 8/8 integration tested, 8/8 live tested, 8/8 spec compliant
