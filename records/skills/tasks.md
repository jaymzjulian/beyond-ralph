# Skills Module Tasks

## Overview

The skills module provides Claude Code skill definitions for the `/beyond-ralph` commands.

**Dependencies**: orchestrator
**Required By**: plugin
**Location**: `src/beyond_ralph/skills/__init__.py`
**Tests**: `tests/unit/test_skills_module.py`
**Status**: COMPLETE (implementation & mock tests)

---

## Task: Implement /beyond-ralph:start Skill

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: Start a new Beyond Ralph project from specification.

**Acceptance Criteria**:
1. Accept spec file path as argument
2. Validate spec file exists
3. Initialize orchestrator
4. Start Phase 1 execution
5. Return status to Claude Code UI
6. Handle errors gracefully

**Tests**: tests/unit/test_skills_module.py::TestStartSkill
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/start-skill/

---

## Task: Implement /beyond-ralph:resume Skill

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: Resume a paused or interrupted project.

**Acceptance Criteria**:
1. Find existing orchestrator state
2. Validate state is resumable
3. Call orchestrator.resume()
4. Continue from checkpoint
5. Show current status
6. Handle "no project" error

**Tests**: tests/unit/test_skills_module.py::TestResumeSkill
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/resume-skill/

---

## Task: Implement /beyond-ralph:status Skill

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: Show current project status.

**Acceptance Criteria**:
1. Read orchestrator state
2. Show current phase
3. Show quota status
4. Show completed/remaining tasks
5. Show recent agent activity
6. Format for Claude Code UI

**Tests**: tests/unit/test_skills_module.py::TestStatusSkill
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/status-skill/

---

## Task: Implement /beyond-ralph:pause Skill

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: Manually pause current project.

**Acceptance Criteria**:
1. Check project is running
2. Call orchestrator.pause()
3. Save current state
4. Show pause confirmation
5. Handle "not running" case
6. Clean up active agents

**Tests**: tests/unit/test_skills_module.py::TestPauseSkill
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/pause-skill/

---

## Task: Implement YAML Skill Definitions

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: YAML skill definition files for .claude/skills/.

**Acceptance Criteria**:
1. Create .claude/skills/beyond-ralph.yaml
2. Define skill name and description
3. Define trigger patterns
4. Define arguments and options
5. Link to Python implementation
6. Follow Claude Code skill format

**Tests**: tests/unit/test_skills_module.py::TestYAMLDefinitions
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/yaml-definitions/

---

## Task: Implement Skill Registration

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [x] Integration tested - 2024-02-02
- [x] Live tested - 2026-02-03 (commands working)
- [x] Spec compliant - 2026-02-03

**Description**: Register skills with Claude Code.

**Acceptance Criteria**:
1. Entry points in pyproject.toml
2. Auto-discovery on install
3. Version compatibility check
4. Skill unregistration on uninstall
5. Error handling for registration
6. Logging for debugging

**Tests**: tests/unit/test_skills_module.py::TestRegistration
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/skills/evidence/registration/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| /beyond-ralph:start Skill | [x] | [x] | [x] | [x] | [x] | [x] |
| /beyond-ralph:resume Skill | [x] | [x] | [x] | [x] | [x] | [x] |
| /beyond-ralph:status Skill | [x] | [x] | [x] | [x] | [x] | [x] |
| /beyond-ralph:pause Skill | [x] | [x] | [x] | [x] | [x] | [x] |
| YAML Skill Definitions | [x] | [x] | [x] | [x] | [x] | [x] |
| Skill Registration | [x] | [x] | [x] | [x] | [x] | [x] |

**Overall Progress**: 6/6 implemented, 6/6 mock tested, 6/6 integration tested, 6/6 live tested, 6/6 spec compliant
