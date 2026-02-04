# Agents Module Tasks

## Overview

The agents module defines all agent types including base classes, phase agents 1-8, and trust model agents.

**Dependencies**: knowledge, session
**Required By**: orchestrator
**Location**: `src/beyond_ralph/agents/`
**Tests**: `tests/unit/test_agents.py`, `tests/unit/test_phase_agents.py`
**Status**: COMPLETE (implementation & mock tests)

---

## Task: Implement BaseAgent Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Base class for all agents with common functionality.

**Acceptance Criteria**:
1. `name`: Agent identifier
2. `description`: What the agent does
3. `model`: AgentModel (OPUS, SONNET, HAIKU)
4. `execute(task)`: Main execution method
5. Core principles injection in prompts
6. Knowledge base integration

**Tests**: tests/unit/test_agents.py::TestBaseAgent
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/base-agent/

---

## Task: Implement PhaseAgent Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Base class for phase-specific agents.

**Acceptance Criteria**:
1. Extends BaseAgent
2. `phase_number`: 1-8
3. `phase_name`: Human-readable name
4. `next_phase()`: Returns next phase agent
5. `can_transition()`: Check if ready for next phase
6. Phase-specific prompt templates

**Tests**: tests/unit/test_agents.py::TestPhaseAgent
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/phase-agent/

---

## Task: Implement TrustModelAgent Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Agent with trust model role flags.

**Acceptance Criteria**:
1. Extends BaseAgent
2. `can_implement`: Boolean (Coding role)
3. `can_test`: Boolean (Testing role)
4. `can_review`: Boolean (Review role)
5. Enforce role separation
6. No agent validates its own work

**Tests**: tests/unit/test_agents.py::TestTrustModelAgent
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/trust-model-agent/

---

## Task: Implement Phase 1-2 Agents

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: SpecAgent (Phase 1) and InterviewAgent (Phase 2).

**Acceptance Criteria**:
1. SpecAgent: Ingest specification, identify features
2. SpecAgent: Create questions for interview phase
3. InterviewAgent: Use AskUserQuestion tool
4. InterviewAgent: Be incredibly in-depth
5. InterviewAgent: Insist on getting needed information
6. InterviewAgent: Store decisions in knowledge base

**Tests**: tests/unit/test_phase_agents.py::TestPhase1_2
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/phase-1-2/

---

## Task: Implement Phase 3-4 Agents

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: SpecCreationAgent (Phase 3) and PlanningAgent (Phase 4).

**Acceptance Criteria**:
1. SpecCreationAgent: Create modular specification
2. SpecCreationAgent: Split into implementable modules
3. SpecCreationAgent: Define module interfaces
4. PlanningAgent: Create project plan with milestones
5. PlanningAgent: Include testing plans
6. PlanningAgent: Create records/[module]/ structure

**Tests**: tests/unit/test_phase_agents.py::TestPhase3_4
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/phase-3-4/

---

## Task: Implement Phase 5-6 Agents

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: UncertaintyReviewAgent (Phase 5) and ValidationAgent (Phase 6).

**Acceptance Criteria**:
1. UncertaintyReviewAgent: Identify uncertainties
2. UncertaintyReviewAgent: Return to Phase 2 if needed
3. UncertaintyReviewAgent: Document resolved questions
4. ValidationAgent: SEPARATE from planning agent
5. ValidationAgent: Validate project plan
6. ValidationAgent: Provide validation evidence

**Tests**: tests/unit/test_phase_agents.py::TestPhase5_6
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/phase-5-6/

---

## Task: Implement Phase 7-8 Agents

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: ImplementationAgent (Phase 7) and TestingValidationAgent (Phase 8).

**Acceptance Criteria**:
1. ImplementationAgent: TDD approach
2. ImplementationAgent: Test its own work
3. ImplementationAgent: Update records with checkboxes
4. TestingValidationAgent: SEPARATE from implementation
5. TestingValidationAgent: Validate with evidence
6. TestingValidationAgent: Can return to Phase 7

**Tests**: tests/unit/test_phase_agents.py::TestPhase7_8
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/phase-7-8/

---

## Task: Implement SpecComplianceAgent

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Verify implementation matches specification.

**Acceptance Criteria**:
1. SEPARATE from implementation and testing agents
2. Compare implementation against spec
3. Verify all spec requirements met
4. Can REMOVE Implemented checkbox
5. Provide compliance evidence
6. List any discrepancies

**Tests**: tests/unit/test_agents.py::TestSpecComplianceAgent
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/spec-compliance/

---

## Task: Implement AgentModel Enum

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Model selection for agents.

**Acceptance Criteria**:
1. OPUS: Most capable (complex reasoning)
2. SONNET: Balanced (default)
3. HAIKU: Fastest (simple tasks)
4. Model-specific flags
5. CLI argument mapping
6. Cost/performance tradeoffs documented

**Tests**: tests/unit/test_agents.py::TestAgentModel
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/agent-model/

---

## Task: Implement AgentTask and AgentResult

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Data structures for agent input/output.

**Acceptance Criteria**:
1. AgentTask: task, context, constraints
2. AgentResult: result, status, evidence
3. Serialization for persistence
4. Knowledge base entries from result
5. Error information in result
6. Duration tracking

**Tests**: tests/unit/test_agents.py::TestAgentTaskResult
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/task-result/

---

## Task: Implement Core Principles Injection

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [ ] Live tested
- [ ] Spec compliant

**Description**: Inject CORE_PRINCIPLES into all agent prompts.

**Acceptance Criteria**:
1. NEVER FAKE RESULTS principle
2. NEVER SILENT FALLBACKS principle
3. NEVER HIDE ERRORS principle
4. NEVER SKIP VERIFICATION principle
5. NEVER GENERATE DISHONEST CODE principle
6. Principles in system prompt for all agents

**Tests**: tests/unit/test_agents.py::TestCorePrinciples
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/agents/evidence/core-principles/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| BaseAgent Class | [x] | [x] | [x] | [x] | [ ] | [ ] |
| PhaseAgent Class | [x] | [x] | [x] | [x] | [ ] | [ ] |
| TrustModelAgent Class | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Phase 1-2 Agents | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Phase 3-4 Agents | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Phase 5-6 Agents | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Phase 7-8 Agents | [x] | [x] | [x] | [x] | [ ] | [ ] |
| SpecComplianceAgent | [x] | [x] | [x] | [x] | [ ] | [ ] |
| AgentModel Enum | [x] | [x] | [x] | [x] | [ ] | [ ] |
| AgentTask and AgentResult | [x] | [x] | [x] | [x] | [ ] | [ ] |
| Core Principles Injection | [x] | [x] | [x] | [x] | [ ] | [ ] |

**Overall Progress**: 11/11 implemented, 11/11 mock tested, 11/11 integration tested, 0/11 live tested, 0/11 spec compliant
