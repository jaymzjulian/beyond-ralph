# Dynamic Plan Module Tasks

## Overview

The dynamic-plan module provides inter-module requirement tracking, allowing modules to add requirements to other modules dynamically.

**Dependencies**: orchestrator, records
**Required By**: orchestrator
**Location**: `src/beyond_ralph/core/dynamic_plan.py`
**Tests**: `tests/unit/test_dynamic_plan.py` (15 tests)
**LOC**: 636

---

## Task: Implement DynamicPlanManager Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Main class for managing dynamic inter-module requirements.

**Acceptance Criteria**:
1. `DynamicPlanManager` class
2. Track requirements between modules
3. Auto-update PROJECT_PLAN.md
4. Notify orchestrator of new requirements
5. Thread-safe operations
6. Persist state to disk

**Tests**: tests/unit/test_dynamic_plan.py::TestDynamicPlanManager
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/plan-manager/

---

## Task: Implement ModuleRequirement Dataclass

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Dataclass for inter-module requirements.

**Acceptance Criteria**:
1. `ModuleRequirement` dataclass with:
   - `source_module`: Module requesting
   - `target_module`: Module that must deliver
   - `requirement`: Technical requirement description
   - `created_at`: Timestamp
   - `status`: PENDING/FULFILLED/FAILED
   - `created_by_session`: UUID of requesting session
2. Serialize to/from JSON
3. Validate requirement is technical (not user-facing)

**Tests**: tests/unit/test_dynamic_plan.py::TestModuleRequirement
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/module-requirement/

---

## Task: Implement add_requirement Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Add new requirement from one module to another.

**Acceptance Criteria**:
1. `add_requirement(source, target, requirement)` adds requirement
2. NO user input required (technical only)
3. Must be specific (not vague)
4. Update PROJECT_PLAN.md automatically
5. Notify orchestrator
6. Log requirement creation

**Tests**: tests/unit/test_dynamic_plan.py::TestAddRequirement
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/add-requirement/

---

## Task: Implement get_pending_requirements Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Get pending requirements for orchestrator.

**Acceptance Criteria**:
1. `get_pending_requirements()` returns PENDING requirements
2. Filter by target module
3. Sort by creation time
4. Include source module info
5. Used by orchestrator to schedule work

**Tests**: tests/unit/test_dynamic_plan.py::TestGetPendingRequirements
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/get-pending/

---

## Task: Implement get_work_for_module Method

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Get scheduled work for a specific module.

**Acceptance Criteria**:
1. `get_work_for_module(module)` returns work items
2. Include both original tasks and dynamic requirements
3. Prioritize by dependency order
4. Include deadline if applicable
5. Used by implementation agents

**Tests**: tests/unit/test_dynamic_plan.py::TestGetWorkForModule
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/get-work/

---

## Task: Implement Discrepancy Tracking

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Track discrepancies between promised and delivered.

**Acceptance Criteria**:
1. `report_discrepancy(module, expected, actual)` records mismatch
2. `Discrepancy` dataclass with severity levels (CRITICAL, HIGH, MEDIUM, LOW)
3. `mark_failed(requirement)` when module fails to deliver
4. Modules MUST call out failures aggressively
5. Update PROJECT_PLAN.md with discrepancy notes
6. Orchestrator mediates resolution

**Tests**: tests/unit/test_dynamic_plan.py::TestDiscrepancyTracking
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/discrepancy-tracking/

---

## Task: Implement PROJECT_PLAN.md Auto-Update

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (plan updates working)
- [x] Spec compliant - 2026-02-03

**Description**: Automatically update PROJECT_PLAN.md with new requirements.

**Acceptance Criteria**:
1. Parse existing PROJECT_PLAN.md
2. Insert new requirements in appropriate section
3. Update module dependencies
4. Preserve existing content
5. Add requirement notes with timestamps
6. PROJECT_PLAN.md is LIVING document

**Tests**: tests/unit/test_dynamic_plan.py::TestProjectPlanUpdate
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/dynamic-plan/evidence/plan-update/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| DynamicPlanManager Class | [x] | [x] | [x] | [x] | [x] | [x] |
| ModuleRequirement Dataclass | [x] | [x] | [x] | [x] | [x] | [x] |
| add_requirement Method | [x] | [x] | [x] | [x] | [x] | [x] |
| get_pending_requirements Method | [x] | [x] | [x] | [x] | [x] | [x] |
| get_work_for_module Method | [x] | [x] | [x] | [x] | [x] | [x] |
| Discrepancy Tracking | [x] | [x] | [x] | [x] | [x] | [x] |
| PROJECT_PLAN.md Auto-Update | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 7/7 implemented, 7/7 mock tested, 7/7 integration tested, 7/7 live tested, 7/7 spec compliant
