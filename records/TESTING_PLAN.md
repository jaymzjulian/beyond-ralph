# Beyond Ralph - Consolidated Testing Plan

## Overview

This document provides the comprehensive testing strategy for Beyond Ralph, covering unit, integration, and live testing requirements for all modules.

---

## Test Pyramid

```
                    +-------------------+
                    |   Live Tests      |  <- Real Claude Code environment
                    |   (~20 tests)     |  <- Quota checking, multi-session
                    +---------+---------+
                              |
               +--------------+--------------+
               |    Integration Tests        |  <- Cross-module interactions
               |    (~50 tests)              |  <- Workflow validation
               +--------------+--------------+
                              |
        +---------------------+---------------------+
        |            Unit Tests                     |  <- Single function/class
        |            (865+ tests, 94.3% coverage)   |  <- Mocked dependencies
        +-------------------------------------------+
```

---

## Unit Test Plan

### Current Status

| Module | Test File | Tests | Coverage | Target |
|--------|-----------|-------|----------|--------|
| utils | test_system.py | 34 | 92% | 95% |
| records-system | test_records.py | 45 | 99% | 95% |
| quota | test_quota_manager.py | 38 | 96% | 95% |
| knowledge | test_knowledge.py | 42 | 98% | 95% |
| session | test_session_manager.py | 51 | 91% | 95% |
| agents/base | test_agents.py | 48 | 92% | 95% |
| phase-agents | test_phase_agents.py | 65 | 99% | 95% |
| research | test_research_agent.py | 42 | 94% | 95% |
| **code-review** | test_review_agent.py | 80 | 94% | **95%** |
| orchestrator | test_orchestrator.py | 72 | 93% | 95% |
| dynamic-plan | test_dynamic_plan.py | 28 | 95% | 95% |
| user-interaction | test_user_interaction.py | 24 | 96% | 95% |
| review-loop | test_review_loop.py | 32 | 94% | 95% |
| skills | test_skills_module.py | 28 | 93% | 95% |
| hooks | test_hooks.py | 22 | 91% | 95% |
| cli | test_cli.py | 18 | 93% | 95% |
| testing | test_testing_skills.py | 35 | 92% | 95% |
| notifications | test_notifications.py | 48 | 99% | 95% |

**Total**: 865+ tests, 94.3% overall coverage

### Unit Test Requirements Per Module

Each module requires:
1. **Happy path tests** - Normal operation
2. **Error handling tests** - Exception scenarios
3. **Edge case tests** - Boundary conditions
4. **Mock tests** - External dependencies mocked

### Code Review Module - Additional Tests Needed

The blocking code-review module needs **145+ additional tests**:

| Component | Current | Needed | Description |
|-----------|---------|--------|-------------|
| Multi-Language Linting | 10 | 60 | Each linter class (JS, TS, Go, Rust, Java, C) |
| Security Scanning | 5 | 40 | Semgrep, Bandit, detect-secrets, Safety |
| Finding Aggregation | 0 | 45 | Deduplication, ranking, grouping, export |

---

## Integration Test Plan

### Test Scenarios

| ID | Scenario | Modules Covered | Priority |
|----|----------|-----------------|----------|
| IT-001 | Full Phase Workflow | orchestrator, all agents, session, knowledge | P0 |
| IT-002 | Quota Pause and Resume | quota, orchestrator, session | P0 |
| IT-003 | Session Lock Handling | session, orchestrator | P0 |
| IT-004 | Dynamic Plan Updates | dynamic-plan, orchestrator, records | P1 |
| IT-005 | Review Loop Cycles | review-loop, code-review, orchestrator | P1 |
| IT-006 | Knowledge Sharing | knowledge, agents, orchestrator | P1 |
| IT-007 | Compaction Recovery | orchestrator, knowledge, records | P1 |

### IT-001: Full Phase Workflow

**Location**: `tests/integration/test_workflow.py`

**Steps**:
1. Initialize orchestrator with test specification
2. Execute Phase 1 (Spec ingestion)
3. Execute Phase 2 (Interview - mock responses)
4. Execute Phase 3 (Modular spec creation)
5. Execute Phase 4 (Project planning)
6. Execute Phase 5 (Uncertainty review)
7. Execute Phase 6 (Validation)
8. Execute Phase 7 (Implementation)
9. Execute Phase 8 (Testing validation)
10. Verify all phases complete successfully

**Pass Criteria**:
- All phases complete without error
- Knowledge entries created with UUIDs
- Records updated with checkboxes
- State persisted and recoverable

**Estimated Duration**: 5-10 minutes

### IT-002: Quota Pause and Resume

**Location**: `tests/integration/test_live_quota.py`

**Steps**:
1. Start orchestrator normally
2. Simulate 85% quota (mock `claude /usage`)
3. Verify orchestrator enters PAUSE state
4. Simulate quota reset (below 85%)
5. Verify orchestrator resumes
6. Complete phase successfully

**Pass Criteria**:
- No failures on high quota
- Clean pause/resume cycle
- State preserved across pause
- Log entries show pause/resume events

### IT-003: Session Lock Handling

**Location**: `tests/integration/test_live_session.py`

**Steps**:
1. Spawn session with lock
2. Attempt second spawn (should fail)
3. Complete first session
4. Verify lock released
5. Second spawn succeeds

**Pass Criteria**:
- Lock prevents duplicate sessions
- Clean cleanup on completion
- No orphaned locks
- Error message on duplicate attempt

### IT-004: Dynamic Plan Updates

**Steps**:
1. Module A adds requirement to Module B
2. Orchestrator detects new requirement
3. Module B work is scheduled
4. Module B delivers requirement
5. Module A completes

**Pass Criteria**:
- Requirements flow between modules
- PROJECT_PLAN.md updated
- Discrepancies tracked
- Orchestrator reacts to failures

### IT-005: Review Loop Cycles

**Steps**:
1. Submit code with known issues
2. Review agent finds issues
3. Fix prompt generated
4. Fixes applied
5. Re-review executed
6. Loop until approval

**Pass Criteria**:
- Review finds all issues
- Fix prompts are actionable
- Loop continues until clean
- Approval granted when fixed

### IT-006: Knowledge Sharing

**Steps**:
1. Agent A writes knowledge entry
2. Agent B reads knowledge entry
3. Verify UUID attribution
4. Search for entry
5. List recent entries

**Pass Criteria**:
- Knowledge persists across agents
- UUID attribution correct
- Search returns correct results
- Recent entries for compaction recovery

### IT-007: Compaction Recovery

**Steps**:
1. Run orchestrator to Phase 4
2. Simulate compaction (clear context)
3. Trigger recovery protocol
4. Verify state restored
5. Continue from correct phase

**Pass Criteria**:
- PROJECT_PLAN.md re-read
- Records re-read
- Knowledge entries loaded
- Correct phase resumed

---

## Live Test Plan

### Environment Requirements

| Requirement | Description |
|-------------|-------------|
| Claude Code | Working Claude Code installation |
| Quota | Sufficient quota for testing (check `br-quota`) |
| Permissions | Accept permission prompts or use --dangerously-skip-permissions |
| Network | Internet access for Claude API |

### Live Test Scenarios

| ID | Test | Module | Evidence Required |
|----|------|--------|-------------------|
| LT-001 | Platform detection | utils | Screenshot of output |
| LT-002 | Quota status check | quota | Screenshot of `br-quota` |
| LT-003 | Session spawning | session | Session output log |
| LT-004 | Knowledge CRUD | knowledge | Knowledge file created |
| LT-005 | /beyond-ralph start | skills | Screenshot of command |
| LT-006 | /beyond-ralph status | skills | Screenshot of status |
| LT-007 | Stop hook | hooks | Log showing hook fired |
| LT-008 | Full workflow (Phase 1-8) | orchestrator | Complete execution log |
| LT-009 | Code review output | code-review | Review findings output |
| LT-010 | Quota pausing | quota | Pause/resume log |

### Evidence Collection

All live tests must collect evidence in:
```
docs/evidence/live/[module]/
├── screenshots/
├── logs/
└── artifacts/
```

Evidence required for each test:
1. **Screenshot** - Visual proof of operation
2. **Log excerpt** - Relevant log output
3. **Artifact** - Created/modified files

---

## Testing Commands

### Run All Unit Tests
```bash
uv run pytest tests/unit -v --cov=src/beyond_ralph --cov-report=term-missing
```

### Run Specific Module Tests
```bash
# Foundation tier
uv run pytest tests/unit/test_system.py tests/unit/test_records.py -v

# Core infrastructure
uv run pytest tests/unit/test_quota_manager.py tests/unit/test_knowledge.py tests/unit/test_session_manager.py -v

# Agent framework
uv run pytest tests/unit/test_agents.py tests/unit/test_phase_agents.py tests/unit/test_research_agent.py tests/unit/test_review_agent.py -v

# Orchestration
uv run pytest tests/unit/test_orchestrator.py tests/unit/test_dynamic_plan.py tests/unit/test_user_interaction.py tests/unit/test_review_loop.py -v

# Integration
uv run pytest tests/unit/test_skills_module.py tests/unit/test_hooks.py tests/unit/test_cli.py -v
```

### Run Integration Tests
```bash
uv run pytest tests/integration -v
```

### Run with Coverage Report
```bash
uv run pytest tests/unit -v --cov=src/beyond_ralph --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Type Checking
```bash
uv run mypy src --strict
```

### Run Linting
```bash
uv run ruff check src tests
uv run ruff format src tests --check
```

---

## Test Quality Gates

### Gate 1: Unit Test Gate (Pre-Merge)

**Triggered**: Before any PR merge

**Criteria**:
- [ ] All unit tests pass
- [ ] Coverage ≥ 80% for changed files
- [ ] Type checking passes (mypy strict)
- [ ] Linting clean (ruff)

### Gate 2: Integration Test Gate (Pre-Live)

**Triggered**: Before Sprint 3 (Live Testing)

**Criteria**:
- [ ] All integration tests pass (IT-001 to IT-007)
- [ ] No flaky tests (3 consecutive passes)
- [ ] Cross-module interactions verified

### Gate 3: Live Test Gate (Pre-Compliance)

**Triggered**: Before Sprint 4 (Spec Compliance)

**Criteria**:
- [ ] All live tests pass (LT-001 to LT-010)
- [ ] Evidence collected for each test
- [ ] Quota handling verified

### Gate 4: Release Gate (Pre-v1.0)

**Triggered**: Before v1.0 tag

**Criteria**:
- [ ] All modules have 6/6 checkboxes
- [ ] Clean install works
- [ ] Documentation complete

---

## Test Data and Fixtures

### Test Specification Files

Location: `tests/fixtures/`

- `simple_spec.md` - Basic specification for quick tests
- `complex_spec.md` - Full specification for integration tests
- `malformed_spec.md` - Invalid specification for error handling

### Mock Data

Location: `tests/fixtures/mocks/`

- `claude_usage_normal.txt` - Normal quota response
- `claude_usage_limited.txt` - 85%+ quota response
- `linter_outputs/` - Mock linter output files

### Test Projects

Location: `test_projects/`

- `python_simple/` - Simple Python project
- `multi_language/` - Project with multiple languages
- `security_issues/` - Project with known security issues

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest tests/unit -v --cov=src/beyond_ralph
      - run: uv run mypy src --strict
      - run: uv run ruff check src tests
```

---

## Troubleshooting

### Common Test Failures

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Import errors | Missing dependency | `uv sync` |
| Type errors | Missing type stubs | `uv add types-xxx` |
| Mock failures | API changed | Update mock expectations |
| Async timeout | Event loop issue | Check `pytest-asyncio` config |
| Coverage drop | New code untested | Add tests for new code |

### Running Tests in Isolation

```bash
# Single test
uv run pytest tests/unit/test_orchestrator.py::TestStateMachine::test_initial_state -v

# Single module
uv run pytest tests/unit/test_orchestrator.py -v

# With verbose output
uv run pytest tests/unit -v --tb=long

# Stop on first failure
uv run pytest tests/unit -x
```

---

*Last Updated: 2026-02-02*
