# Beyond Ralph - Comprehensive Project Plan

## Project Vision

Create a fully autonomous multi-agent development system for Claude Code that implements the Spec and Interview Coder methodology, running for DAYS if needed to deliver complete projects.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Module Dependency Graph](#module-dependency-graph)
3. [Implementation Order](#implementation-order)
4. [Phase Milestones](#phase-milestones)
5. [Testing Strategy](#testing-strategy)
6. [Integration Test Plan](#integration-test-plan)
7. [Risk Mitigation](#risk-mitigation)
8. [Module Status Summary](#module-status-summary)
9. [Critical Path Analysis](#critical-path-analysis)
10. [Dynamic Requirements](#dynamic-requirements)
11. [Sprint Planning](#sprint-planning)
12. [Release Criteria](#release-criteria)

---

## Quick Start for Developers

### Before Starting Any Work

```bash
# 1. Sync dependencies
cd /home/jaymz/beyond-ralph
uv sync

# 2. Verify environment
uv run pytest tests/unit -q --tb=no  # All tests should pass
uv run mypy src --no-error-summary    # No type errors
uv run ruff check src tests           # No lint errors

# 3. Check current status
git status
cat PROJECT_PLAN.md | head -100       # Review blocking items
```

### Daily Workflow

| Step | Action | Command/Location |
|------|--------|------------------|
| 1 | Check blocking items | `PROJECT_PLAN.md` → "Blocking Items" |
| 2 | Pick task from current sprint | `PROJECT_PLAN.md` → "Sprint Planning" |
| 3 | Read task specification | `records/[module]/tasks.md` |
| 4 | Implement with TDD | Write test → Implement → Pass |
| 5 | Update checkboxes | `records/[module]/tasks.md` |
| 6 | Run verification | `uv run pytest && uv run mypy src` |
| 7 | Commit with convention | `git commit -m "feat(module): description"` |

### Current Priority (What to Work On NOW)

**P0 BLOCKING (Must complete before anything else):**
1. `records/code-review/tasks.md` → Multi-Language Linting task
2. `records/code-review/tasks.md` → Security Scanning task
3. `records/code-review/tasks.md` → Finding Aggregation task

**P1 NEXT (After P0 complete):**
1. Run integration tests IT-001 through IT-007
2. Live testing in Claude Code environment
3. SpecComplianceAgent verification

---

## Executive Summary

**Project Status**: 95% Implementation Complete, Testing & Validation Required

**Key Metrics**:
- Total Modules: 20
- Implemented: 19/20 (95%)
- Unit Tests: 865+ passing (94.3% coverage)
- Integration Tests: 3 test files with 7 scenarios (IT-001 to IT-007)
- Live Tests: Pending (tests/live/)
- Spec Compliance: Pending validation by SpecComplianceAgent

**Blocking Items (P0 - Must Fix)**:
1. **CodeReviewAgent Multi-Language Linting** - JS/TS, Go, Rust, Java, C/C++ support
2. **CodeReviewAgent Security Scanning** - Full Semgrep OWASP integration
3. **CodeReviewAgent Finding Aggregation** - Deduplication and report generation
4. **Integration Test Execution** - Run IT-001 through IT-007
5. **Live Testing** - Test in real Claude Code environment
6. **Spec Compliance Verification** - SpecComplianceAgent must verify all modules

**Release Path**:
```
Sprint 1 (Current) → Sprint 2 → Sprint 3 → Sprint 4 → Sprint 5 → v1.0
Code Review Fix    Integration  Live Test   Spec       Docs/Release
2-3 days           2 days       2-3 days    1-2 days   1-2 days
```

**Next Milestone**: Complete code-review module blocking tasks

---

## Module Dependency Graph

```
                              +------------------------------------------+
                              |           TIER 0: FOUNDATION             |
                              |           (No Dependencies)              |
                              |  +-------------+    +-----------------+  |
                              |  |   utils     |    |  records-system |  |
                              |  |  (system)   |    |   (tracking)    |  |
                              |  +------+------+    +--------+--------+  |
                              |         |                    |           |
                              +---------+--------------------+-----------+
                                        |                    |
                    +-------------------+--------------------+-------------------+
                    |                   v                    v                   |
                    |        TIER 1: CORE INFRASTRUCTURE                        |
                    |        (Foundation Required)                              |
                    |  +-------------+  +-------------+  +-----------------+   |
                    |  |   quota     |  |  knowledge  |  |    session      |   |
                    |  |  manager    |  |    base     |  |    manager      |   |
                    |  +------+------+  +------+------+  +--------+--------+   |
                    |         |                |                  |            |
                    +---------+----------------+------------------+------------+
                              |                |                  |
                    +---------+----------------+------------------+------------+
                    |         v                v                  v            |
                    |    TIER 2: AGENT FRAMEWORK                               |
                    |    (Core Required)                                       |
                    |  +---------------------------------------------------+   |
                    |  |                   base agents                     |   |
                    |  |    (BaseAgent, PhaseAgent, TrustModelAgent)       |   |
                    |  +------------------------+--------------------------+   |
                    |         +----------------+----------------+               |
                    |         v                v                v               |
                    |  +-------------+ +-------------+ +-----------------+     |
                    |  |   phase     | |  research   | |   code-review   |     |
                    |  |  agents 1-8 | |    agent    | |     agent       |     |
                    |  +-------------+ +-------------+ +-----------------+     |
                    +------------------------+-------------------------------+
                                             |
                    +------------------------+-------------------------------+
                    |                        v                               |
                    |    TIER 3: ORCHESTRATION                               |
                    |    (Agents Required)                                   |
                    |  +--------------------------------------------------+  |
                    |  |                orchestrator                      |  |
                    |  |  (phase transitions, quota checks, delegation)   |  |
                    |  +------------------------+-------------------------+  |
                    |         +----------------+----------------+             |
                    |         v                v                v             |
                    |  +-------------+ +-------------+ +-----------------+    |
                    |  |  dynamic    | |    user     | |    review       |    |
                    |  |   plan      | | interaction | |     loop        |    |
                    |  +-------------+ +-------------+ +-----------------+    |
                    +------------------------+-------------------------------+
                                             |
                    +------------------------+-------------------------------+
                    |                        v                               |
                    |    TIER 4: CLAUDE CODE INTEGRATION                     |
                    |    (Orchestration Required)                            |
                    |  +-------------+  +-------------+  +-----------------+ |
                    |  |   skills    |  |    hooks    |  |     plugin      | |
                    |  |  (/beyond-  |  |   (stop,    |  |   structure     | |
                    |  |   ralph)    |  |   quota)    |  |   (.claude/)    | |
                    |  +-------------+  +-------------+  +-----------------+ |
                    +------------------------+-------------------------------+
                                             |
                    +------------------------+-------------------------------+
                    |                        v                               |
                    |    TIER 5: TESTING & CODE REVIEW                       |
                    |    (Integration Required)                              |
                    |  +-------------+  +-------------+  +-----------------+ |
                    |  |  testing    |  | code-review |  |   system        | |
                    |  |   skills    |  | (complete)  |  |  capabilities   | |
                    |  +-------------+  +-------------+  +-----------------+ |
                    +------------------------+-------------------------------+
                                             |
                    +------------------------+-------------------------------+
                    |                        v                               |
                    |    TIER 6: ADVANCED FEATURES (Optional)                |
                    |  +-------------+  +-------------+  +-----------------+ |
                    |  |notifications|  |   github    |  |    remote       | |
                    |  |   system    |  | integration |  |    access       | |
                    |  +-------------+  +-------------+  +-----------------+ |
                    +--------------------------------------------------------+
```

### Module Dependency Matrix

| Module | Direct Dependencies | Dependents | Criticality |
|--------|---------------------|------------|-------------|
| utils | None | ALL modules | CRITICAL |
| records-system | None | ALL modules | CRITICAL |
| quota | utils | session, orchestrator | HIGH |
| knowledge | utils, records | agents, orchestrator | HIGH |
| session | utils, quota | orchestrator | HIGH |
| agents (base) | knowledge, session | phase agents, orchestrator | HIGH |
| phase-agents | base agents, knowledge | orchestrator | HIGH |
| research | base agents, knowledge | testing, orchestrator | MEDIUM |
| code-review | base agents | orchestrator | **BLOCKING** |
| orchestrator | session, quota, agents | skills, hooks | HIGH |
| dynamic-plan | orchestrator, records | orchestrator | MEDIUM |
| user-interaction | orchestrator | skills | MEDIUM |
| review-loop | orchestrator | orchestrator | MEDIUM |
| skills | orchestrator | plugin | HIGH |
| hooks | orchestrator, quota | plugin | HIGH |
| plugin | skills, hooks | end users | HIGH |
| testing | utils, research | orchestrator | HIGH |
| system-capabilities | utils | testing | MEDIUM |
| notifications | orchestrator | autonomous operation | LOW |
| github-integration | orchestrator, session | PR workflows | LOW |
| remote-access | session | distributed operation | LOW |

---

## Implementation Order

Based on module dependencies, implement in this strict order:

### Tier 0: Foundation (No Dependencies) - COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 0.1 | **utils** | DONE | None | All modules | 6 | 24/36 (67%) |
| 0.2 | **records-system** | DONE | None | All modules | 5 | 20/30 (67%) |

### Tier 1: Core Infrastructure (Foundation Required) - COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 1.1 | **quota** | DONE | utils | session, orchestrator | 6 | 24/36 (67%) |
| 1.2 | **knowledge** | DONE | utils, records | agents, orchestrator | 6 | 24/36 (67%) |
| 1.3 | **session** | DONE | utils, quota | orchestrator | 6 | 24/36 (67%) |

### Tier 2: Agent Framework (Core Required) - 95% COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 2.1 | **agents** (base) | DONE | knowledge, session | phase agents, orchestrator | 12 | 48/72 (67%) |
| 2.2 | **research** | DONE | base agents, knowledge | testing, orchestrator | 7 | 28/42 (67%) |
| 2.3 | **code-review** | **PARTIAL** | base agents | orchestrator | 8 | 15/48 (31%) |

### Tier 3: Orchestration (Agents Required) - COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 3.1 | **orchestrator** | DONE | session, quota, agents | skills, hooks | 8 | 32/48 (67%) |
| 3.2 | **dynamic-plan** | DONE | orchestrator, records | orchestrator | 4 | 16/24 (67%) |
| 3.3 | **user-interaction** | DONE | orchestrator | skills | 4 | 16/24 (67%) |
| 3.4 | **review-loop** (core) | DONE | orchestrator | orchestrator | 4 | 16/24 (67%) |

### Tier 4: Claude Code Integration (Orchestration Required) - COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 4.1 | **skills** | DONE | orchestrator | plugin | 6 | 24/36 (67%) |
| 4.2 | **hooks** | DONE | orchestrator, quota | plugin | 5 | 20/30 (67%) |
| 4.3 | **plugin** | DONE | skills, hooks | end users | 3 | 12/18 (67%) |

### Tier 5: Testing & Review (Integration Required) - 90% COMPLETE

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 5.1 | **testing** | DONE | utils, research | orchestrator | 7 | 28/42 (67%) |
| 5.2 | **system-capabilities** | DONE | utils | testing | 4 | 16/24 (67%) |

### Tier 6: Advanced Features (Optional)

| Order | Module | Status | Depends On | Required By | Tasks | Checkboxes |
|-------|--------|--------|------------|-------------|-------|------------|
| 6.1 | **notifications** | DONE | orchestrator | autonomous operation | 6 | 24/36 (67%) |
| 6.2 | **github-integration** | PLANNED | orchestrator, session | PR workflows | 4 | 4/24 (17%) |
| 6.3 | **remote-access** | PLANNED | session | distributed operation | 4 | 4/24 (17%) |

---

## Phase Milestones

### Phase 1: Foundation (Sprint 1) - COMPLETE

**Goal**: Establish project structure and basic utilities

#### Milestone 1.1: Project Setup
- [x] Create directory structure per CLAUDE.md
- [x] Set up pyproject.toml with uv
- [x] Create CLAUDE.md guidelines
- [x] Initialize git repository

#### Milestone 1.2: Utils Module
- [x] Platform detection (Linux, macOS, Windows, WSL2)
- [x] Package manager detection (apt, dnf, pacman, brew, etc.)
- [x] Tool inventory (40+ tools checked)
- [x] Passwordless sudo detection
- [x] Virtual display support (xvfb)

#### Milestone 1.3: Records System
- [x] RecordsManager class
- [x] 6-checkbox tracking per task
- [x] Per-module folder structure
- [x] Evidence collection support

**Exit Criteria**: Unit tests pass, records can track tasks with 6 checkboxes

---

### Phase 2: Core Infrastructure (Sprint 2) - COMPLETE

**Goal**: Session management, quota monitoring, knowledge base

#### Milestone 2.1: Quota Manager
- [x] Parse `claude /usage` output
- [x] Track session and weekly percentages
- [x] File-based caching (5min normal, 10min when limited)
- [x] 85% threshold detection
- [x] PAUSE behavior (not stop)
- [x] `is_unknown` field for honest error handling
- [x] CLI entry point: `br-quota`

#### Milestone 2.2: Knowledge Base
- [x] KnowledgeBase class with CRUD operations
- [x] KnowledgeEntry dataclass with YAML frontmatter
- [x] Session UUID tracking for source attribution
- [x] Search and filter capabilities
- [x] Recent entries listing for compaction recovery

#### Milestone 2.3: Session Manager
- [x] spawn_cli() with pexpect for interactive sessions
- [x] UUID generation and tracking
- [x] Lock file mechanism (prevent duplicate access)
- [x] Result extraction from output
- [x] `--continue` flag support for follow-ups
- [x] SessionOutput class with [AGENT:uuid] formatting

**Exit Criteria**: All unit tests pass, quota checking works, sessions can spawn

---

### Phase 3: Agent Framework (Sprint 3) - 95% COMPLETE

**Goal**: Define all agent types and their behaviors

#### Milestone 3.1: Base Agent Classes (COMPLETE)
- [x] BaseAgent with name, description, model selection
- [x] PhaseAgent extending BaseAgent with phase number
- [x] TrustModelAgent with can_implement/can_test/can_review flags
- [x] AgentModel enum (OPUS, SONNET, HAIKU)
- [x] AgentTask and AgentResult dataclasses
- [x] Core principles injection in prompts

#### Milestone 3.2: Phase Agents 1-8 (COMPLETE)
- [x] Phase 1: SpecAgent - Specification ingestion
- [x] Phase 2: InterviewAgent - User interview with AskUserQuestion
- [x] Phase 3: SpecCreationAgent - Modular spec creation
- [x] Phase 4: PlanningAgent - Project planning with milestones
- [x] Phase 5: UncertaintyReviewAgent - Uncertainty identification
- [x] Phase 6: ValidationAgent - Plan validation
- [x] Phase 7: ImplementationAgent - TDD implementation
- [x] Phase 8: TestingValidationAgent - Test execution

#### Milestone 3.3: Trust Model Agents (PARTIAL - BLOCKING)
- [x] SpecComplianceAgent - Verify implementation matches spec
- [x] CodeReviewAgent - Language detection, structure
- [ ] **BLOCKING**: CodeReviewAgent - Full multi-language linting
- [x] ResearchAgent - Tool discovery framework
- [x] ResearchAgent - PREFERRED_TOOLS dictionary

**Exit Criteria**: All agents can execute, trust model enforced

---

### Phase 4: Orchestration (Sprint 4) - COMPLETE

**Goal**: Main control loop and coordination

#### Milestone 4.1: Core Orchestrator
- [x] Orchestrator class with state machine
- [x] start(), resume(), pause(), status() methods
- [x] Phase transitions (1 through 8)
- [x] Quota check before each agent interaction
- [x] Session locking verification

#### Milestone 4.2: Dynamic Plan Manager
- [x] DynamicPlanManager class
- [x] ModuleRequirement dataclass
- [x] add_requirement() for inter-module dependencies
- [x] Discrepancy tracking between promised and delivered
- [x] PROJECT_PLAN.md auto-update

#### Milestone 4.3: User Interaction
- [x] UserInteractionManager class
- [x] Question routing from subagents
- [x] Response submission
- [x] Progress update streaming

#### Milestone 4.4: Review Loop
- [x] ReviewLoopManager class
- [x] ReviewItem and ReviewCycle dataclasses
- [x] generate_fix_prompt() for coder agent
- [x] verify_fix() for re-review
- [x] Loop until approval

**Exit Criteria**: Full workflow can execute from phase 1 to phase 8

---

### Phase 5: Claude Code Integration (Sprint 5) - COMPLETE

**Goal**: Native Claude Code experience

#### Milestone 5.1: Skills
- [x] /beyond-ralph:start - Start new project
- [x] /beyond-ralph:resume - Resume paused project
- [x] /beyond-ralph:status - Check current status
- [x] /beyond-ralph:pause - Manual pause
- [x] YAML skill definitions in .claude/skills/

#### Milestone 5.2: Hooks
- [x] stop.yaml - Persist state on session end
- [x] quota-check.yaml - Pre-tool quota enforcement
- [x] subagent_stop.py - Handle subagent completion
- [x] Hook registration in .claude/hooks/

#### Milestone 5.3: Plugin Structure
- [x] Complete .claude/ directory structure
- [x] Entry points in pyproject.toml
- [x] Self-contained packaging

**Exit Criteria**: /beyond-ralph commands work in Claude Code

---

### Phase 6: Testing & Code Review (Sprint 6) - IN PROGRESS

**Goal**: Comprehensive testing and code quality enforcement

#### Milestone 6.1: Testing Skills (COMPLETE)
- [x] TestRunner class for pytest, playwright
- [x] TestingSkills for API, web, CLI, desktop GUI
- [x] MockAPIServer for development testing
- [x] Screenshot analysis for GUI testing
- [x] TestEvidence class

#### Milestone 6.2: Code Review Agent (PARTIAL - BLOCKING)
- [x] CodeReviewAgent class scaffold
- [x] Language detection (14+ languages)
- [x] ReviewSeverity and ReviewCategory enums
- [ ] **BLOCKING**: Multi-language linter orchestration
- [ ] **BLOCKING**: Semgrep OWASP integration
- [ ] **BLOCKING**: Finding aggregation

#### Milestone 6.3: System Capabilities (COMPLETE)
- [x] install_system_package() with sudo
- [x] install_browser_testing_deps()
- [x] install_build_tools()
- [x] detect_available_tools()

**Exit Criteria**: All test types work, code review produces findings

---

### Phase 7: Live Testing & Polish (Sprint 7) - PENDING

**Goal**: Validate in real Claude Code environment

#### Milestone 7.1: Integration Testing
- [ ] Run all integration test scenarios (IT-001 to IT-006)
- [ ] Validate cross-module interactions
- [ ] Test error handling and recovery
- [ ] Achieve 100% integration test pass rate

#### Milestone 7.2: Live Testing
- [ ] Test in Claude Code environment
- [ ] Collect evidence for each module
- [ ] Verify quota handling works
- [ ] Test all 8 phases in sequence

#### Milestone 7.3: Spec Compliance
- [ ] Run SpecComplianceAgent on all modules
- [ ] Verify implementations match specifications
- [ ] Document any discrepancies
- [ ] Fix all non-compliant implementations

#### Milestone 7.4: Documentation
- [ ] Complete user documentation
- [ ] Complete developer documentation
- [ ] Process evidence compilation
- [ ] Release notes

**Exit Criteria**: All modules have 6/6 checkboxes checked

---

## Testing Strategy

### Test Pyramid

```
                    +-------------------+
                    |   Live Tests      |  <- Real Claude Code
                    |   (End-to-End)    |  <- Quota checking
                    |   ~20 tests       |  <- Multi-session
                    +---------+---------+
                              |
               +--------------+--------------+
               |    Integration Tests        |  <- Module interactions
               |    (Cross-Module)           |  <- Workflow tests
               |    ~50 tests                |  <- State persistence
               +--------------+--------------+
                              |
        +---------------------+---------------------+
        |            Unit Tests                     |  <- Single functions
        |            (Per-Module)                   |  <- Mocked dependencies
        |            ~500 tests                     |  <- Fast execution
        +-------------------------------------------+
```

### Test Categories

| Category | Location | Runner | Coverage Target | Status |
|----------|----------|--------|-----------------|--------|
| Unit | tests/unit/ | pytest | 90%+ | 500+ tests |
| Integration | tests/integration/ | pytest | Key workflows | 50+ tests |
| Live | tests/live/ | br-live-tests | Critical paths | Planned |

### 6-Checkbox Testing Flow

```
1. Planned      -> Design review, spec written
2. Implemented  -> Code written, linting passes
3. Mock Tested  -> Unit tests pass (mocked deps)
4. Integration  -> Integration tests pass (real deps)
5. Live Tested  -> Works in Claude Code environment
6. Spec Compliant -> SpecComplianceAgent verifies
```

### Test Commands

```bash
# Unit tests (fast, mocked)
uv run pytest tests/unit -v --cov=src/beyond_ralph

# Integration tests (slower, real interactions)
uv run pytest tests/integration -v

# Live tests (requires Claude Code)
uv run br-live-tests

# All tests
uv run pytest tests/ -v --cov=src/beyond_ralph

# Type checking
uv run mypy src --strict

# Linting
uv run ruff check src tests
```

---

## Integration Test Plan

### Test Suite Overview

| Suite | File | Modules Covered | Priority |
|-------|------|-----------------|----------|
| Workflow | test_workflow.py | orchestrator, agents, session | P0 |
| Quota | test_live_quota.py | quota, orchestrator | P0 |
| Session | test_live_session.py | session, hooks | P0 |

### Integration Test Scenarios

#### IT-001: Full Phase Workflow
**Modules**: orchestrator, agents (all phases), session, knowledge
**Description**: Test complete flow from spec ingestion to testing validation

**Steps**:
1. Initialize orchestrator with test spec
2. Execute Phase 1 (Spec ingestion)
3. Execute Phase 2 (Interview - mock responses)
4. Execute Phase 3 (Spec creation)
5. Execute Phase 4 (Planning)
6. Execute Phase 5 (Uncertainty review)
7. Execute Phase 6 (Validation)
8. Execute Phase 7 (Implementation)
9. Execute Phase 8 (Testing)
10. Verify all phases complete successfully

**Pass Criteria**:
- All phases complete without error
- Knowledge entries created with UUIDs
- Records updated with checkboxes
- State persisted and recoverable

#### IT-002: Quota Pause and Resume
**Modules**: quota, orchestrator, session
**Description**: Verify PAUSE behavior at 85% quota

**Steps**:
1. Start orchestrator normally
2. Simulate 85% quota (mock)
3. Verify orchestrator enters PAUSE state
4. Simulate quota reset
5. Verify orchestrator resumes
6. Complete phase successfully

**Pass Criteria**:
- No failures on high quota
- Clean pause/resume
- State preserved across pause
- Log entries show pause/resume events

#### IT-003: Session Lock Handling
**Modules**: session, orchestrator
**Description**: Verify lock files prevent duplicate access

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

#### IT-004: Dynamic Plan Updates
**Modules**: dynamic-plan, orchestrator, records
**Description**: Verify inter-module requirements work

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

#### IT-005: Review Loop Cycles
**Modules**: review-loop, code-review, orchestrator
**Description**: Verify fix loop until approval

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

#### IT-006: Knowledge Sharing
**Modules**: knowledge, agents, orchestrator
**Description**: Verify agents share knowledge across sessions

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

#### IT-007: Compaction Recovery
**Modules**: orchestrator, knowledge, records
**Description**: Verify recovery after context compaction

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

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Claude CLI changes** | Medium | High | Abstract CLI layer; version pinning | Switch to Task tool |
| **Quota detection unreliable** | Medium | High | Conservative 85% threshold; `is_unknown` blocks | Manual quota check |
| **Session spawning fails** | Low | High | Retry with backoff; pexpect handling | Fallback to Task tool |
| **Context compaction** | High | Medium | Compaction recovery protocol | Checkpoint/resume |
| **Linter tool missing** | Medium | Medium | Research agent finds alternatives | Fallback linters |
| **pexpect platform issues** | Low | Medium | Use subprocess fallback on Windows | Alternative CLI driver |
| **Lock file corruption** | Low | Low | 5-minute timeout; force unlock | Manual lock removal |

### Operational Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Long-running tests fail** | Medium | Medium | Checkpoint state; resume capability | Manual intervention |
| **Tool installation fails** | Medium | Low | Research agent finds alternatives | Manual installation |
| **Rate limiting** | High | Medium | Quota-aware pausing; 10-minute retry | Wait for reset |
| **Network failures** | Medium | Low | Retry logic; offline fallbacks | Queue for later |
| **Disk space** | Low | Medium | Evidence cleanup; rotation | Manual cleanup |

### Project Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Scope creep** | Medium | Medium | Clear spec checkboxes; PR reviews | Defer to future |
| **Integration complexity** | Medium | High | Modular design; explicit deps | Incremental integration |
| **Code review incomplete** | High | High | Prioritize BLOCKING items | Temporary skip |
| **Documentation debt** | Medium | Low | Document as you go | Post-release docs |
| **External dependency changes** | Low | Medium | Pin versions; abstract layers | Update adapters |

### Contingency Plans

1. **If CLI breaks**: Switch to Task tool mode for agent spawning
2. **If quota always unknown**: Assume 0% with warning; proceed cautiously
3. **If session lock stuck**: 5-minute timeout; force unlock with warning
4. **If compaction occurs**: Re-read PROJECT_PLAN.md, records/, knowledge/
5. **If code review tool fails**: Research agent finds alternative linter
6. **If integration tests hang**: Timeout after 5 minutes; collect partial results
7. **If live tests fail**: Document failure; flag for manual testing

### Risk Monitoring

| Risk Category | Monitoring Method | Alert Threshold |
|---------------|-------------------|-----------------|
| Quota | br-quota check | >75% session or weekly |
| Session Health | Lock file age | >30 minutes |
| Test Failures | pytest exit code | Any failure |
| Build Health | ruff/mypy | Any error |
| Knowledge Base | Entry count | <5 entries after Phase 2 |

---

## Module Status Summary

| Module | Planned | Implemented | Mock | Integration | Live | Spec | Overall |
|--------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|---------|
| utils | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| records-system | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| quota | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| knowledge | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| session | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| agents | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| research | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| orchestrator | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| dynamic-plan | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| user-interaction | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| core (review-loop) | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| **code-review** | [x] | **[~]** | **[~]** | [ ] | [ ] | [ ] | **31%** |
| skills | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| hooks | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| plugin | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| testing | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| system-capabilities | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| notifications | [x] | [x] | [x] | [x] | [ ] | [ ] | 67% |
| github-integration | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | 17% |
| remote-access | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | 17% |

**Legend**: [x] = Complete, [~] = Partial, [ ] = Not Complete

---

## Critical Path Analysis

The critical path to v1.0 release:

```
Foundation -> Core Infrastructure -> Agent Framework -> Orchestration -> Integration -> Live
    |               |                    |                |              |           |
    v               v                    v                v              v           v
  utils          quota              agents/base       orchestrator    skills      live tests
  records        knowledge          phase 1-8         dynamic-plan    hooks       evidence
                 session            trust model       review-loop     plugin      docs
                                    research          user-interact
                                    code-review*
                                           ^
                                    BLOCKING ITEM
```

### Blocking Items for Release

| Priority | Item | Module | Status | Action Required | Owner |
|----------|------|--------|--------|-----------------|-------|
| P0 | Complete multi-language linting | code-review | PARTIAL | Implement run_linters() | TBD |
| P0 | Complete security scanning | code-review | PARTIAL | Integrate Semgrep OWASP | TBD |
| P0 | Complete finding aggregation | code-review | NOT STARTED | Implement aggregation logic | TBD |
| P0 | Run integration test suite | all | PLANNED | Execute IT-001 to IT-007 | TBD |
| P0 | Live testing in Claude Code | all | PLANNED | Collect evidence | TBD |
| P1 | SpecComplianceAgent verification | agents | PLANNED | Verify all modules | TBD |
| P1 | Documentation updates | docs | PLANNED | Complete user/dev docs | TBD |
| P2 | GitHub integration | github | PLANNED | Optional for v1.0 | TBD |
| P2 | Remote access | remote | PLANNED | Optional for v1.0 | TBD |

### Unblocking Strategy

```
1. IMMEDIATELY: Complete CodeReviewAgent
   - Multi-language linting (JS/TS, Go, Rust)
   - Semgrep OWASP integration
   - Finding aggregation

2. THEN: Run Integration Tests
   - Execute IT-001 through IT-007
   - Fix any failures
   - Mark integration checkboxes

3. THEN: Live Testing
   - Test in Claude Code environment
   - Collect evidence
   - Mark live checkboxes

4. FINALLY: Spec Compliance
   - Run SpecComplianceAgent on all modules
   - Fix non-compliant items
   - Mark spec checkboxes
```

---

## Dynamic Requirements

### Active Requirements (Pending Delivery)

| ID | From Module | To Module | Requirement | Status | Priority |
|----|-------------|-----------|-------------|--------|----------|
| DR-001 | orchestrator | code-review | Multi-language linter support | PENDING | P0 |
| DR-002 | orchestrator | code-review | Semgrep OWASP integration | PENDING | P0 |
| DR-003 | orchestrator | code-review | Finding aggregation | PENDING | P0 |

### Delivered Requirements

| ID | From Module | To Module | Requirement | Delivered | Verified |
|----|-------------|-----------|-------------|-----------|----------|
| DR-100 | agents | session | UUID-based session tracking | 2026-02-01 | Yes |
| DR-101 | orchestrator | quota | 85% pause threshold | 2026-02-01 | Yes |
| DR-102 | testing | research | Tool discovery framework | 2026-02-01 | Yes |

### Discrepancies

| ID | Module | Promised | Actual | Severity | Status |
|----|--------|----------|--------|----------|--------|
| DISC-001 | code-review | Multi-language linting | Python only | HIGH | OPEN |
| DISC-002 | code-review | Full OWASP scanning | Partial | HIGH | OPEN |

---

## Sprint Planning

### Sprint Overview

| Sprint | Focus | Duration | Exit Criteria |
|--------|-------|----------|---------------|
| **Sprint 1** | Code Review Completion | 2-3 days | All code-review tasks implemented & tested |
| **Sprint 2** | Integration Testing | 2 days | IT-001 to IT-007 all pass |
| **Sprint 3** | Live Testing | 2-3 days | All modules work in Claude Code |
| **Sprint 4** | Spec Compliance | 1-2 days | SpecComplianceAgent verifies all |
| **Sprint 5** | Documentation & Release | 1-2 days | v1.0 packaged and released |

---

### Sprint 1: Code Review Completion (CURRENT)

**Duration**: 2-3 days
**Focus**: Complete all blocking code-review tasks
**Owner**: Implementation Agent
**Validator**: Review Agent

#### Sprint 1 Goals
1. Complete CodeReviewAgent multi-language support
2. Complete security scanning integration
3. Complete finding aggregation
4. Expand unit tests to 150+ for code-review module

#### Sprint 1 Tasks (Day-by-Day)

**Day 1: Multi-Language Linting**
- [ ] `JavaScriptLinter` class
  - eslint JSON output parsing
  - jshint fallback
  - standard fallback
  - Tests: 10+ unit tests
- [ ] `TypeScriptLinter` class
  - tsc diagnostic parsing
  - eslint+ts fallback
  - deno lint fallback
  - Tests: 10+ unit tests
- [ ] `GoLinter` class
  - staticcheck JSON parsing
  - golint fallback
  - go vet fallback
  - Tests: 10+ unit tests

**Day 2: Multi-Language Linting (continued) + Security**
- [ ] `RustLinter` class
  - cargo clippy JSON parsing
  - rustfmt --check fallback
  - Tests: 8+ unit tests
- [ ] `JavaLinter` class
  - checkstyle XML parsing
  - pmd fallback
  - spotbugs fallback
  - Tests: 8+ unit tests
- [ ] `CLinter` class
  - clang-tidy parsing
  - cppcheck fallback
  - gcc -Wall fallback
  - Tests: 8+ unit tests
- [ ] `LinterRegistry` class
  - Auto-select by detected language
  - Fallback chain execution
  - Tests: 5+ unit tests
- [ ] Begin Semgrep OWASP integration
  - Ruleset downloading (p/owasp-top-ten)
  - Basic SARIF output parsing

**Day 3: Security Scanning + Finding Aggregation**
- [ ] Complete Semgrep integration
  - Multi-language security scanning
  - OWASP severity mapping
  - Tests: 10+ unit tests
- [ ] Bandit integration (Python security)
  - JSON output parsing
  - Severity mapping
  - Tests: 5+ unit tests
- [ ] detect-secrets integration
  - Secret detection across files
  - Tests: 5+ unit tests
- [ ] `FindingAggregator` class
  - Deduplication (same issue from multiple tools)
  - Severity ranking (CRITICAL > HIGH > MEDIUM > LOW > INFO)
  - File-based grouping
  - Markdown report generation
  - JSON export
  - Tests: 15+ unit tests

#### Sprint 1 Acceptance Criteria
1. ✅ `CodeReviewAgent.review(files)` returns findings for 6+ languages
2. ✅ Security findings include OWASP rule references
3. ✅ Findings sorted by severity, grouped by file
4. ✅ All existing tests still passing
5. ✅ Coverage stays above 90%
6. ✅ 150+ unit tests for code-review module

#### Sprint 1 Deliverables
- [ ] `src/beyond_ralph/agents/linters/` directory with 6 linter classes
- [ ] `src/beyond_ralph/agents/security/` directory with security scanners
- [ ] `src/beyond_ralph/agents/aggregation.py` for finding aggregation
- [ ] Updated `tests/unit/test_review_agent.py` with 150+ tests
- [ ] `records/code-review/tasks.md` with all 8 tasks at Implemented ✓

---

### Sprint 2: Integration Testing

**Duration**: 2 days
**Focus**: Execute all integration tests
**Owner**: Testing Agent
**Validator**: SpecComplianceAgent

#### Sprint 2 Goals
1. Run all integration test scenarios
2. Fix any cross-module failures
3. Mark all modules "Integration tested"

#### Sprint 2 Tasks

**Day 1: Core Integration Tests**
- [ ] IT-001: Full Phase Workflow
  - All 8 phases in sequence
  - Knowledge entries created
  - Records updated
  - State persisted
- [ ] IT-002: Quota Pause and Resume
  - 85% quota triggers PAUSE
  - Clean pause/resume
  - State preserved
- [ ] IT-003: Session Lock Handling
  - Lock prevents duplicate sessions
  - Clean cleanup on completion
  - No orphaned locks

**Day 2: Advanced Integration Tests**
- [ ] IT-004: Dynamic Plan Updates
  - Requirements flow between modules
  - PROJECT_PLAN.md updated
  - Discrepancies tracked
- [ ] IT-005: Review Loop Cycles
  - Review finds all issues
  - Fix prompts actionable
  - Loop until clean
- [ ] IT-006: Knowledge Sharing
  - Knowledge persists across agents
  - UUID attribution correct
  - Search works
- [ ] IT-007: Compaction Recovery
  - PROJECT_PLAN.md re-read
  - Records re-read
  - Correct phase resumed

#### Sprint 2 Acceptance Criteria
1. ✅ All 7 integration tests pass
2. ✅ No flaky tests (3 consecutive passes)
3. ✅ Integration test coverage report generated
4. ✅ Evidence in `docs/evidence/integration/`

#### Sprint 2 Deliverables
- [ ] `docs/evidence/integration/` with test outputs
- [ ] All modules marked "Integration tested" in tasks.md
- [ ] Integration test summary report

---

### Sprint 3: Live Testing

**Duration**: 2-3 days
**Focus**: Test in real Claude Code environment
**Owner**: Live Testing Agent
**Validator**: Human + SpecComplianceAgent

#### Sprint 3 Goals
1. Test each module in Claude Code
2. Collect evidence (screenshots, logs)
3. Mark all modules "Live tested"

#### Sprint 3 Tasks

**Day 1: Foundation & Core**
- [ ] utils module live test
  - Platform detection works
  - Tool inventory accurate
  - Screenshot evidence
- [ ] records-system live test
  - Checkboxes update correctly
  - Evidence paths work
- [ ] quota module live test
  - Real `claude /usage` parsing
  - 85% threshold triggers pause
  - Screenshot evidence
- [ ] knowledge module live test
  - Entries created with UUIDs
  - Search works
- [ ] session module live test
  - Sessions spawn correctly
  - `[AGENT:uuid]` output prefix visible
  - Lock files work

**Day 2: Agents & Orchestration**
- [ ] agents module live test
  - Phase agents execute
  - Trust model enforced
- [ ] orchestrator module live test
  - Full workflow Phase 1-8
  - Quota checking works
  - Compaction recovery works
- [ ] Code review live test
  - Multi-language linting works
  - Security findings correct
  - Screenshot of review output

**Day 3: Claude Code Integration**
- [ ] skills module live test
  - `/beyond-ralph start` works
  - `/beyond-ralph status` shows info
  - Screenshot evidence
- [ ] hooks module live test
  - Stop hook persists state
  - Quota hook blocks at limit
- [ ] plugin module live test
  - Clean install works
  - Skills register correctly

#### Sprint 3 Acceptance Criteria
1. ✅ `/beyond-ralph start` works in Claude Code
2. ✅ Quota pausing works with real Claude quotas
3. ✅ Subagent output streams to main session
4. ✅ Full workflow completes Phase 1-8
5. ✅ Evidence in `docs/evidence/live/`

#### Sprint 3 Deliverables
- [ ] `docs/evidence/live/[module]/` for each module
- [ ] Screenshots for key operations
- [ ] All modules marked "Live tested" in tasks.md

---

### Sprint 4: Spec Compliance

**Duration**: 1-2 days
**Focus**: Verify all implementations match specifications
**Owner**: SpecComplianceAgent
**Validator**: Human review

#### Sprint 4 Goals
1. SpecComplianceAgent verifies each module
2. Fix any discrepancies
3. Mark all modules "Spec compliant"

#### Sprint 4 Tasks

**Day 1: Compliance Verification**
- [ ] Run SpecComplianceAgent on Tier 0-3 modules
  - utils, records-system
  - quota, knowledge, session
  - agents, research, code-review
  - orchestrator, dynamic-plan, user-interaction, review-loop
- [ ] Document discrepancies found
- [ ] Fix any critical discrepancies

**Day 2: Final Compliance + Fixes**
- [ ] Run SpecComplianceAgent on Tier 4-6 modules
  - skills, hooks, plugin
  - testing, system-capabilities
  - notifications
- [ ] Fix remaining discrepancies
- [ ] Mark all tasks "Spec compliant"

#### Sprint 4 Acceptance Criteria
1. ✅ Every module has 6/6 checkboxes
2. ✅ No spec discrepancies remain
3. ✅ SPEC.md requirements traced to code
4. ✅ Verification evidence in records

#### Sprint 4 Deliverables
- [ ] Spec compliance report per module
- [ ] All modules at 6/6 checkboxes
- [ ] `records/*/tasks.md` fully checked

---

### Sprint 5: Documentation & Release

**Duration**: 1-2 days
**Focus**: Documentation and package for release
**Owner**: Documentation Agent
**Validator**: Human review

#### Sprint 5 Goals
1. Complete user documentation
2. Complete developer documentation
3. Package and release v1.0

#### Sprint 5 Tasks

**Day 1: Documentation**
- [ ] User guide (`docs/user/guide.md`)
  - Installation
  - Quick start
  - Commands reference
  - Troubleshooting
- [ ] Developer guide (`docs/developer/guide.md`)
  - Architecture overview
  - Contributing guide
  - API reference
  - Testing guide

**Day 2: Release**
- [ ] Release notes (`CHANGELOG.md`)
- [ ] Clean install test on fresh Ubuntu
- [ ] Clean install test on fresh macOS
- [ ] Create v1.0 tag
- [ ] Update README.md

#### Sprint 5 Acceptance Criteria
1. ✅ `uv pip install .` works on clean Ubuntu/macOS
2. ✅ All skills register correctly
3. ✅ Hooks execute without error
4. ✅ Documentation covers all features
5. ✅ README has quick start guide

#### Sprint 5 Deliverables
- [ ] Complete `docs/user/` directory
- [ ] Complete `docs/developer/` directory
- [ ] CHANGELOG.md
- [ ] Git tag v1.0.0
- [ ] Release announcement

---

## Release Criteria

### v1.0 Release Requirements

All of the following MUST be met:

#### Code Quality
- [ ] All unit tests passing (500+)
- [ ] All integration tests passing (IT-001 to IT-007)
- [ ] Code coverage ≥ 80%
- [ ] No critical linting errors
- [ ] Type checking passes (mypy strict)

#### Module Completion
- [ ] All modules have 6/6 checkboxes for core tasks
- [ ] Code review module fully functional
- [ ] Orchestrator completes full workflow

#### Testing
- [ ] Live testing completed in Claude Code
- [ ] Evidence collected for each module
- [ ] SpecComplianceAgent verified all modules

#### Documentation
- [ ] User documentation complete
- [ ] Developer documentation complete
- [ ] CLAUDE.md accurate and up-to-date

#### Packaging
- [ ] `uv pip install .` works on clean system
- [ ] All dependencies in pyproject.toml
- [ ] No external tool dependencies

### Success Criteria

1. **Autonomous Operation**: Runs for DAYS without intervention (except interviews)
2. **Quota Awareness**: PAUSES at 85% (never stops)
3. **Three-Agent Trust**: Coding + Testing + Review for EVERY implementation
4. **6/6 Checkboxes**: ALL tasks have ALL 6 checkboxes checked
5. **Self-Contained**: Installs on clean system with `uv pip install .`
6. **Documentation**: Complete user/developer docs with process evidence
7. **Never Fake Results**: ALL agents follow honest error handling

---

## Module Task Cross-Reference

| Module | Task File | Tasks | Status |
|--------|-----------|-------|--------|
| utils | [records/utils/tasks.md](records/utils/tasks.md) | 6 | DONE |
| records-system | [records/records-system/tasks.md](records/records-system/tasks.md) | 5 | DONE |
| quota | [records/quota/tasks.md](records/quota/tasks.md) | 6 | DONE |
| knowledge | [records/knowledge/tasks.md](records/knowledge/tasks.md) | 6 | DONE |
| session | [records/session/tasks.md](records/session/tasks.md) | 6 | DONE |
| agents | [records/agents/tasks.md](records/agents/tasks.md) | 12 | DONE |
| research | [records/research/tasks.md](records/research/tasks.md) | 7 | DONE |
| code-review | [records/code-review/tasks.md](records/code-review/tasks.md) | 8 | **BLOCKING** |
| orchestrator | [records/orchestrator/tasks.md](records/orchestrator/tasks.md) | 8 | DONE |
| dynamic-plan | [records/dynamic-plan/tasks.md](records/dynamic-plan/tasks.md) | 4 | DONE |
| user-interaction | [records/user-interaction/tasks.md](records/user-interaction/tasks.md) | 4 | DONE |
| core (review-loop) | [records/core/tasks.md](records/core/tasks.md) | 10 | DONE |
| skills | [records/skills/tasks.md](records/skills/tasks.md) | 6 | DONE |
| hooks | [records/hooks/tasks.md](records/hooks/tasks.md) | 5 | DONE |
| plugin | [records/plugin/tasks.md](records/plugin/tasks.md) | 3 | DONE |
| testing | [records/testing/tasks.md](records/testing/tasks.md) | 7 | DONE |
| system-capabilities | [records/system-capabilities/tasks.md](records/system-capabilities/tasks.md) | 4 | DONE |
| notifications | [records/notifications/tasks.md](records/notifications/tasks.md) | 6 | DONE |
| github-integration | [records/github-integration/tasks.md](records/github-integration/tasks.md) | 4 | PLANNED |
| remote-access | [records/remote-access/tasks.md](records/remote-access/tasks.md) | 4 | PLANNED |

---

## Detailed Risk Mitigation Strategies

### Risk 1: Claude CLI Interface Changes

**Risk Level**: Medium-High
**Impact**: Breaking changes could halt all agent spawning

**Detection**:
- Monitor Claude Code release notes weekly
- Automated smoke test on CLI flags
- Version check on startup

**Mitigation Layers**:
1. **Abstraction Layer**: All CLI interactions go through `SessionManager` - single point of change
2. **Version Detection**: Check `claude --version` and adjust flags accordingly
3. **Flag Fallback**: If `--dangerously-skip-permissions` fails, try `--yes` or `--auto-approve`
4. **Task Tool Mode**: Complete fallback implementation using native Task tool instead of CLI

**Recovery Procedure**:
```python
# Recovery steps if CLI breaks
1. Check `claude --version` output
2. Compare against known working versions in config
3. If version mismatch, check known flag mappings
4. If still failing, switch to Task tool mode
5. Log all recovery attempts for debugging
```

### Risk 2: Quota Detection Unreliability

**Risk Level**: Medium
**Impact**: Could spawn agents when quota depleted, wasting user's limits

**Detection**:
- `is_unknown=True` field in QuotaStatus
- Parse error logging
- Response time monitoring (>5s suggests issues)

**Mitigation Layers**:
1. **Conservative Threshold**: 85% (not 95%) gives buffer
2. **Unknown = Limited**: If we can't determine quota, assume limited
3. **Cached Fallback**: Use last known good value for up to 30 minutes
4. **Manual Override**: `br-quota --force-check` bypasses cache

**Recovery Procedure**:
```python
# Recovery steps for quota issues
1. If parse fails, try alternative output formats
2. Check ~/.claude/config.json for quota info
3. If all else fails, set is_unknown=True and PAUSE
4. Notify user: "Unable to verify quota - paused for safety"
5. Wait for user to run manual `claude /usage` check
```

### Risk 3: Session Lock Corruption

**Risk Level**: Low
**Impact**: Orphaned locks prevent new sessions

**Detection**:
- Lock file age >30 minutes
- PID in lock file no longer running
- Multiple lock files for same session

**Mitigation Layers**:
1. **PID Validation**: Check if owning process still alive
2. **Age Timeout**: Auto-clean locks older than 5 minutes
3. **Heartbeat**: Active sessions update lock file timestamp
4. **Force Clean**: `br-cleanup --force-unlock` for manual intervention

**Recovery Procedure**:
```python
# Lock recovery algorithm
def recover_lock(lock_path: Path) -> bool:
    lock_data = read_lock(lock_path)

    # Check if PID still alive
    if not is_pid_running(lock_data.pid):
        remove_lock(lock_path)
        return True

    # Check age
    if lock_data.age > timedelta(minutes=5):
        log.warning(f"Force-removing stale lock: {lock_path}")
        remove_lock(lock_path)
        return True

    # Lock is valid
    return False
```

### Risk 4: Context Compaction Mid-Task

**Risk Level**: High (expected to happen)
**Impact**: Orchestrator loses track of current work

**Detection**:
- Automatic: Watch for context_compacted event
- Manual: PROJECT_PLAN.md not in context
- Heuristic: Agent doesn't remember recent decisions

**Mitigation Layers**:
1. **State Files**: All state persisted to disk, not just context
2. **Recovery Protocol**: MANDATORY re-read sequence after compaction
3. **Knowledge Base**: Critical decisions stored externally
4. **Checkpoint System**: Each phase transition creates checkpoint

**Recovery Procedure** (MANDATORY):
```python
async def compaction_recovery():
    """MUST run after any context compaction."""
    # Step 1: Re-establish ground truth
    project_plan = await read_file("PROJECT_PLAN.md")

    # Step 2: Find current module
    current = await find_in_progress_module_from_records()

    # Step 3: Re-read module context
    module_spec = await read_file(f"records/{current}/spec.md")
    module_tasks = await read_file(f"records/{current}/tasks.md")

    # Step 4: Check recent knowledge
    recent = await knowledge_base.list_recent(hours=24)
    for entry in recent[-5:]:  # Last 5 entries
        await read_file(entry.path)

    # Step 5: Resume from checkpoint
    checkpoint = await load_checkpoint(current)
    await resume_from(checkpoint)
```

### Risk 5: Multi-Language Linter Tool Missing

**Risk Level**: Medium
**Impact**: Code review incomplete for non-Python projects

**Detection**:
- Tool inventory shows linter missing
- Linter command returns error
- Empty results for known-bad code

**Mitigation Layers**:
1. **Research Agent**: Automatically find and install alternatives
2. **Fallback Chain**: Each language has 2-3 alternative linters
3. **Partial Results**: Return available findings, mark incomplete
4. **User Notification**: Alert if no linter available for language

**Linter Fallback Chains**:
```
Python:     ruff -> pylint -> flake8
JavaScript: eslint -> jshint -> standard
TypeScript: tsc -> eslint+ts -> deno lint
Go:         staticcheck -> golint -> go vet
Rust:       cargo clippy -> rustfmt --check
Java:       checkstyle -> pmd -> spotbugs
C/C++:      clang-tidy -> cppcheck -> gcc -Wall
Ruby:       rubocop -> ruby-lint -> reek
```

### Risk 6: Integration Test Timeout/Hang

**Risk Level**: Medium
**Impact**: CI/CD pipeline blocked, unclear failure state

**Detection**:
- Test takes >5 minutes
- No output for >60 seconds
- Memory usage growing unbounded

**Mitigation Layers**:
1. **Per-Test Timeout**: 5 minute max per integration test
2. **Resource Monitoring**: Kill if memory >2GB
3. **Progress Markers**: Each test logs progress every 30 seconds
4. **Partial Results**: Collect what completed before timeout

**Recovery Procedure**:
```python
@pytest.fixture
def integration_test_watchdog():
    """Kill test if it hangs."""
    def watchdog():
        start = time.time()
        while time.time() - start < 300:  # 5 minutes
            time.sleep(30)
            if test_thread.is_alive():
                log.info("Test still running...")
            else:
                return
        # Timeout reached
        collect_partial_results()
        force_kill_test()
        pytest.fail("Test timeout after 5 minutes")
```

---

## Risk Mitigation Decision Matrix

### Quick Reference: What to Do When Things Go Wrong

| Situation | Immediate Action | Recovery Path | Escalation |
|-----------|------------------|---------------|------------|
| Quota at 85% | PAUSE all operations | Wait 10 min, retry | User notification |
| Quota unknown | Assume LIMITED, PAUSE | Manual `claude /usage` | User intervention |
| Session spawn fails | Retry with backoff (3x) | Switch to Task tool mode | Log error, skip |
| Lock file stuck | Check PID, auto-clean >5min | Force remove with warning | Manual cleanup |
| Linter tool missing | Research agent finds alternative | Use fallback chain | Skip with warning |
| Context compaction | MANDATORY recovery protocol | Re-read all key files | Resume from checkpoint |
| Integration test hang | Timeout after 5min | Collect partial results | Manual investigation |
| Live test fails | Document failure | Retry with verbose logging | Manual testing |
| Spec non-compliance | Document discrepancy | Fix and re-verify | Human review |
| Network failure | Retry with exponential backoff | Queue for later | Manual intervention |

### Risk Response Procedures

#### Procedure 1: Quota Exceeded Response
```
1. IMMEDIATELY pause all agent spawning
2. Log current phase and state
3. Set orchestrator state to PAUSED
4. Save checkpoint to disk
5. Start 10-minute timer
6. After timer: check quota again
7. If still limited: repeat from step 5
8. If available: resume from checkpoint
```

#### Procedure 2: Session Failure Response
```
1. Log the error with full context
2. Check if error is transient (retry 3x with 5s backoff)
3. If still failing: check CLI version
4. If version issue: try alternative flags
5. If all else fails: switch to Task tool mode
6. Log the fallback for debugging
```

#### Procedure 3: Compaction Recovery Response
```
1. IMMEDIATELY re-read PROJECT_PLAN.md
2. IMMEDIATELY re-read current module spec
3. IMMEDIATELY re-read task status
4. Load last 5 knowledge entries
5. Verify current phase from state file
6. Resume from last checkpoint
7. Log recovery event
```

#### Procedure 4: Code Review Tool Failure Response
```
1. Log which tool failed and why
2. Check fallback chain for language
3. Try next tool in chain
4. If all tools fail: mark as partial review
5. Research agent searches for new tool
6. Install and retry if found
7. Store result in knowledge base
```

---

## Sprint Breakdown with Clear Deliverables

### Sprint 0: Assessment (COMPLETE)
**Duration**: 1 day
**Goal**: Understand current state

**Deliverables**:
- [x] Codebase exploration complete
- [x] All existing records reviewed
- [x] Blocking items identified (code-review: 3 tasks)
- [x] Test coverage verified (94.3%)
- [x] PROJECT_PLAN.md updated

### Sprint 1: Code Review Completion (CURRENT)
**Duration**: 2-3 days
**Goal**: Complete all blocking code-review tasks

**Deliverables**:
- [ ] Multi-language linting (JS/TS, Go, Rust, Java, C/C++)
- [ ] Semgrep OWASP security scanning
- [ ] Finding aggregation and deduplication
- [ ] Code review unit tests expanded (target: 150 tests)
- [ ] Code review integration tests added

**Acceptance Criteria**:
1. `CodeReviewAgent.review(files)` returns findings for 6+ languages
2. Security findings include OWASP rule references
3. Findings sorted by severity, grouped by file
4. All existing tests still passing
5. Coverage stays above 90%

**Daily Goals**:
- Day 1: Multi-language linting (eslint, staticcheck, clippy)
- Day 2: Security scanning (Semgrep OWASP)
- Day 3: Finding aggregation + tests

### Sprint 2: Integration Testing
**Duration**: 2 days
**Goal**: Execute all integration tests

**Deliverables**:
- [ ] IT-001: Full phase workflow test
- [ ] IT-002: Quota pause/resume test
- [ ] IT-003: Session lock handling test
- [ ] IT-004: Dynamic plan updates test
- [ ] IT-005: Review loop cycles test
- [ ] IT-006: Knowledge sharing test
- [ ] IT-007: Compaction recovery test
- [ ] All modules marked "Integration tested"

**Acceptance Criteria**:
1. All 7 integration tests pass
2. No flaky tests (run 3x each)
3. Integration test coverage report generated
4. Evidence stored in `docs/evidence/integration/`

### Sprint 3: Live Testing
**Duration**: 2-3 days
**Goal**: Test in real Claude Code environment

**Deliverables**:
- [ ] Live testing environment set up
- [ ] Each module tested in Claude Code
- [ ] Evidence collected (screenshots, logs)
- [ ] All modules marked "Live tested"

**Acceptance Criteria**:
1. `/beyond-ralph start` works in Claude Code
2. Quota pausing works with real Claude quotas
3. Subagent output streams to main session
4. Full workflow completes Phase 1-8
5. Evidence stored in `docs/evidence/live/`

### Sprint 4: Spec Compliance
**Duration**: 1-2 days
**Goal**: Verify all implementations match specifications

**Deliverables**:
- [ ] SpecComplianceAgent verifies each module
- [ ] Discrepancies documented and fixed
- [ ] All modules marked "Spec compliant"
- [ ] Final verification report

**Acceptance Criteria**:
1. Every module has 6/6 checkboxes
2. No spec discrepancies remain
3. SPEC.md requirements all traced to code
4. Verification evidence in records

### Sprint 5: Documentation & Release
**Duration**: 1-2 days
**Goal**: Complete documentation and package for release

**Deliverables**:
- [ ] User documentation complete
- [ ] Developer documentation complete
- [ ] Release notes written
- [ ] Package tested on clean system
- [ ] v1.0 tag created

**Acceptance Criteria**:
1. `uv pip install .` works on clean Ubuntu/macOS
2. All skills register correctly
3. Hooks execute without error
4. Documentation covers all features
5. README has quick start guide

---

## Module Acceptance Criteria Summary

### Tier 0: Foundation
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **utils** | Platform detection for Linux/macOS/Windows/WSL2; 40+ tools inventoried; passwordless sudo detected |
| **records-system** | 6 checkboxes per task; checkbox state can be removed by testing/spec agents; evidence path tracking |

### Tier 1: Core Infrastructure
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **quota** | Parse `claude /usage`; 85% threshold triggers PAUSE; `is_unknown=True` blocks operations |
| **knowledge** | YAML frontmatter; session UUID attribution; `list_recent(hours=24)` for compaction recovery |
| **session** | pexpect spawning; `[AGENT:uuid]` output prefix; lock files with PID; `--continue` for follow-ups |

### Tier 2: Agent Framework
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **agents/base** | BaseAgent, PhaseAgent, TrustModelAgent; AgentModel enum; core principles injection |
| **phase-agents** | All 8 phases implemented; transitions validated; knowledge stored after each phase |
| **research** | PREFERRED_TOOLS dict; autonomous fallback on tool failure; knowledge base storage |
| **code-review** | 14+ language detection; multi-language linting; OWASP security scanning; finding aggregation |

### Tier 3: Orchestration
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **orchestrator** | State machine (IDLE→RUNNING→PAUSED→COMPLETE); quota check before every agent; compaction recovery |
| **dynamic-plan** | Inter-module requirements; PROJECT_PLAN.md auto-update; discrepancy tracking |
| **user-interaction** | AskUserQuestion routing; response delivery; progress streaming |
| **review-loop** | Fix loop until approval; ALL review items non-negotiable; evidence collection |

### Tier 4: Claude Code Integration
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **skills** | `/beyond-ralph:start`, `:resume`, `:status`, `:pause`; YAML definitions; entry points registered |
| **hooks** | Stop hook persists state; quota hook blocks at 85%; subagent completion handled |
| **plugin** | Complete `.claude/` structure; self-contained packaging; no external dependencies |

### Tier 5: Testing & Review
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **testing** | API, Web, CLI, Desktop GUI testing; TestEvidence class; ClaudeDriver for live tests |
| **system-capabilities** | Package installation with sudo; browser deps; build tools |

### Tier 6: Advanced (Optional for v1.0)
| Module | Key Acceptance Criteria |
|--------|-------------------------|
| **notifications** | Slack, Discord, Email providers; event-based; retry logic |
| **github-integration** | PR creation workflow; issue tracking |
| **remote-access** | Distributed agent operation |

---

## Quality Gates

### Gate 1: Unit Test Gate
**When**: Before any PR merge
**Criteria**:
- All unit tests pass (`uv run pytest tests/unit`)
- Coverage ≥ 80% for changed files
- Type checking passes (`uv run mypy src`)
- Linting clean (`uv run ruff check src tests`)

### Gate 2: Integration Test Gate
**When**: Before Sprint 3 (Live Testing)
**Criteria**:
- All integration tests pass (IT-001 to IT-007)
- No flaky tests (3 consecutive passes)
- Cross-module interactions verified

### Gate 3: Live Test Gate
**When**: Before Sprint 4 (Spec Compliance)
**Criteria**:
- All modules work in Claude Code
- Quota handling verified with real quotas
- Evidence collected for each module

### Gate 4: Release Gate
**When**: Before v1.0 tag
**Criteria**:
- All modules have 6/6 checkboxes
- Clean install works (`uv pip install .`)
- Documentation complete
- No critical/high severity issues open

---

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unit Tests | 500+ | 865+ | ✅ EXCEEDS |
| Test Coverage | 80%+ | 94.3% | ✅ EXCEEDS |
| Integration Tests | 50+ | 11 | ⚠️ NEEDS WORK |
| Live Tests | 20+ | 0 | 🔴 PENDING |
| Modules Complete (6/6) | 20 | 0 | 🔴 PENDING |
| Documentation Pages | 10+ | 5 | ⚠️ NEEDS WORK |

---

---

## Pre-Flight Checklists

### Before Starting Implementation Sprint

- [ ] All unit tests passing (`uv run pytest tests/unit -v`)
- [ ] Type checking clean (`uv run mypy src --strict`)
- [ ] Linting clean (`uv run ruff check src tests`)
- [ ] Git working tree clean (`git status`)
- [ ] On correct branch (develop or feature branch)
- [ ] Read current sprint tasks in `PROJECT_PLAN.md`
- [ ] Read task specifications in `records/[module]/tasks.md`

### Before Integration Testing

- [ ] All P0 blocking items resolved
- [ ] All unit tests passing with 90%+ coverage
- [ ] All type errors resolved
- [ ] All modules have "Mock tested" checkbox checked
- [ ] Integration test files exist in `tests/integration/`

### Before Live Testing

- [ ] All integration tests passing (IT-001 to IT-007)
- [ ] Claude Code environment available
- [ ] Sufficient quota available (check `br-quota`)
- [ ] Live test scripts ready in `tests/live/`
- [ ] Evidence collection folders created

### Before Release (v1.0)

- [ ] ALL modules have 6/6 checkboxes checked
- [ ] Code review module fully functional (no blocking items)
- [ ] Clean install works (`uv pip install .` on fresh system)
- [ ] All documentation complete in `docs/`
- [ ] Release notes written
- [ ] No critical/high severity issues open
- [ ] SpecComplianceAgent verified all modules

---

## Module Verification Commands

Quick commands to verify each module tier:

```bash
# Tier 0: Foundation
uv run pytest tests/unit/test_system.py tests/unit/test_records.py -v

# Tier 1: Core Infrastructure
uv run pytest tests/unit/test_quota_manager.py tests/unit/test_knowledge.py tests/unit/test_session_manager.py -v

# Tier 2: Agent Framework
uv run pytest tests/unit/test_agents.py tests/unit/test_phase_agents.py tests/unit/test_research_agent.py tests/unit/test_review_agent.py -v

# Tier 3: Orchestration
uv run pytest tests/unit/test_orchestrator.py tests/unit/test_dynamic_plan.py tests/unit/test_user_interaction.py tests/unit/test_review_loop.py -v

# Tier 4: Claude Code Integration
uv run pytest tests/unit/test_skills_module.py tests/unit/test_hooks.py tests/unit/test_cli.py -v

# Tier 5: Testing & Review
uv run pytest tests/unit/test_testing_skills.py tests/unit/test_claude_driver.py -v

# All tests with coverage
uv run pytest tests/unit -v --cov=src/beyond_ralph --cov-report=term-missing
```

---

## Troubleshooting Common Issues

### Tests Failing

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Import errors | Missing dependency | `uv sync` |
| Type errors | Missing type stubs | `uv add types-xxx` |
| Mock failures | API changed | Update mock expectations |
| Timeout | Async issue | Check `pytest-asyncio` config |

### Build Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| `uv sync` fails | Lock file issue | `uv lock --upgrade` |
| mypy errors | Missing hints | Add type annotations |
| ruff errors | Style issue | `uv run ruff check --fix` |

### Live Testing Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Quota exceeded | Hit rate limit | Wait for reset or use `br-quota --wait` |
| Session lock | Previous crash | `rm .beyond_ralph_sessions/*.lock` |
| Hook not firing | Registration issue | Check `.claude/hooks/` |

---

## Appendix A: Complete Module List with Files

| Module | Source File(s) | Test File(s) | Tasks File |
|--------|----------------|--------------|------------|
| utils | `src/beyond_ralph/utils/system.py` | `tests/unit/test_system.py` | `records/utils/tasks.md` |
| records-system | `src/beyond_ralph/core/records.py` | `tests/unit/test_records.py` | `records/records-system/tasks.md` |
| quota | `src/beyond_ralph/core/quota_manager.py` | `tests/unit/test_quota_manager.py` | `records/quota/tasks.md` |
| knowledge | `src/beyond_ralph/core/knowledge.py` | `tests/unit/test_knowledge.py` | `records/knowledge/tasks.md` |
| session | `src/beyond_ralph/core/session_manager.py` | `tests/unit/test_session_manager.py` | `records/session/tasks.md` |
| agents | `src/beyond_ralph/agents/base.py` | `tests/unit/test_agents.py` | `records/agents/tasks.md` |
| phase-agents | `src/beyond_ralph/agents/phase_agents.py` | `tests/unit/test_phase_agents.py` | `records/agents/tasks.md` |
| research | `src/beyond_ralph/agents/research_agent.py` | `tests/unit/test_research_agent.py` | `records/research/tasks.md` |
| code-review | `src/beyond_ralph/agents/review_agent.py` | `tests/unit/test_review_agent.py` | `records/code-review/tasks.md` |
| orchestrator | `src/beyond_ralph/core/orchestrator.py` | `tests/unit/test_orchestrator.py` | `records/orchestrator/tasks.md` |
| dynamic-plan | `src/beyond_ralph/core/dynamic_plan.py` | `tests/unit/test_dynamic_plan.py` | `records/dynamic-plan/tasks.md` |
| user-interaction | `src/beyond_ralph/core/user_interaction.py` | `tests/unit/test_user_interaction.py` | `records/user-interaction/tasks.md` |
| review-loop | `src/beyond_ralph/core/review_loop.py` | `tests/unit/test_review_loop.py` | `records/core/tasks.md` |
| skills | `src/beyond_ralph/skills/__init__.py` | `tests/unit/test_skills_module.py` | `records/skills/tasks.md` |
| hooks | `src/beyond_ralph/hooks/` | `tests/unit/test_hooks.py` | `records/hooks/tasks.md` |
| plugin | `.claude/` | - | `records/plugin/tasks.md` |
| testing | `src/beyond_ralph/testing/` | `tests/unit/test_testing_skills.py` | `records/testing/tasks.md` |
| system-capabilities | `src/beyond_ralph/utils/system.py` | `tests/unit/test_system.py` | `records/system-capabilities/tasks.md` |
| notifications | `src/beyond_ralph/core/notifications.py` | `tests/unit/test_notifications.py` | `records/notifications/tasks.md` |
| github-integration | TBD | TBD | `records/github-integration/tasks.md` |
| remote-access | TBD | TBD | `records/remote-access/tasks.md` |

---

## Appendix B: Testing Evidence Requirements

Each module requires evidence for the "Live tested" checkbox:

| Module | Required Evidence |
|--------|-------------------|
| **utils** | Screenshot of platform detection output |
| **records-system** | Sample tasks.md with updated checkboxes |
| **quota** | Screenshot of `br-quota` output with real quota |
| **knowledge** | Knowledge entries created by agents |
| **session** | Session output with `[AGENT:uuid]` prefix |
| **orchestrator** | Complete phase 1-8 execution log |
| **skills** | Screenshot of `/beyond-ralph status` in Claude Code |
| **hooks** | Log showing hook execution on stop |
| **testing** | Test execution output with coverage |
| **code-review** | Review findings for multi-language project |

Evidence should be stored in `docs/evidence/live/[module]/`.

---

## Appendix C: Commit Message Examples

Follow these patterns for consistent git history:

```bash
# Feature implementations
git commit -m "feat(orchestrator): add phase transition validation"
git commit -m "feat(code-review): implement JavaScript linter integration"

# Bug fixes
git commit -m "fix(session): handle lock file cleanup on crash"
git commit -m "fix(quota): correct percentage parsing for edge cases"

# Tests
git commit -m "test(agents): add integration tests for phase agents"
git commit -m "test(orchestrator): add compaction recovery tests"

# Documentation
git commit -m "docs(readme): add quick start guide"
git commit -m "docs(records): update checkpoint status for code-review"

# Refactoring
git commit -m "refactor(knowledge): extract YAML parsing to separate method"

# Chores
git commit -m "chore(deps): update pydantic to 2.5"
git commit -m "chore(ci): add mypy to pre-commit hooks"
```

---

*This plan covers EVERY item from SPEC.md plus user additions. Nothing is thrown away.*
*Last Updated: 2026-02-02*

---

## Appendix D: Module Testing Requirements

### Unit Test Requirements Per Module

| Module | Minimum Tests | Key Test Areas | Current |
|--------|---------------|----------------|---------|
| utils | 30 | Platform detection, tool inventory | 34 |
| records-system | 15 | CRUD operations, 6-checkbox | 16 |
| quota | 60 | Parsing, thresholds, caching | 65 |
| knowledge | 15 | YAML operations, search | 18 |
| session | 40 | Spawning, locks, output formatting | 47 |
| agents/base | 20 | Agent classes, model selection | 22 |
| phase-agents | 25 | All 8 phases | 30 |
| research | 40 | Tool discovery, installation | 48 |
| code-review | 100 | Multi-language linting, security | 53 (NEEDS 47 MORE) |
| orchestrator | 35 | State machine, phase transitions | 42 |
| dynamic-plan | 12 | Requirements, discrepancies | 15 |
| user-interaction | 12 | Question routing | 15 |
| review-loop | 15 | Fix cycles, approval | 20 |
| skills | 20 | All 4 skills | 20 |
| hooks | 12 | Stop, quota, subagent | 15 |
| testing | 50 | All testing types | 55 |
| notifications | 25 | All providers | 32 |

---

## Appendix E: Implementation Order by File

Strict order of files to implement/modify:

### Tier 0: Foundation
1. `src/beyond_ralph/utils/system.py` - Platform, package manager, tools
2. `src/beyond_ralph/core/records.py` - 6-checkbox tracking

### Tier 1: Core Infrastructure
3. `src/beyond_ralph/core/quota_manager.py` - Usage limit tracking
4. `src/beyond_ralph/utils/quota_checker.py` - CLI tool
5. `src/beyond_ralph/core/knowledge.py` - Knowledge base
6. `src/beyond_ralph/core/session_manager.py` - Claude CLI sessions

### Tier 2: Agent Framework
7. `src/beyond_ralph/agents/base.py` - Base agent classes
8. `src/beyond_ralph/agents/phase_agents.py` - 8 phase implementations
9. `src/beyond_ralph/agents/research_agent.py` - Tool discovery
10. `src/beyond_ralph/agents/review_agent.py` - Code review **BLOCKING**

### Tier 3: Orchestration
11. `src/beyond_ralph/core/orchestrator.py` - Main control loop
12. `src/beyond_ralph/core/dynamic_plan.py` - Inter-module requirements
13. `src/beyond_ralph/core/user_interaction.py` - Question routing
14. `src/beyond_ralph/core/review_loop.py` - Fix cycles

### Tier 4: Claude Code Integration
15. `src/beyond_ralph/skills/__init__.py` - Skill implementations
16. `src/beyond_ralph/hooks/stop_handler.py` - Stop hook
17. `src/beyond_ralph/hooks/quota_check.py` - Quota hook
18. `src/beyond_ralph/hooks/subagent_stop.py` - Subagent hook
19. `.claude/skills/beyond-ralph.yaml` - Skill definitions
20. `.claude/hooks/*.yaml` - Hook definitions

### Tier 5: Testing
21. `src/beyond_ralph/testing/skills.py` - Test runners
22. `src/beyond_ralph/testing/claude_driver.py` - Live testing

### Tier 6: Optional
23. `src/beyond_ralph/core/notifications.py` - Notifications
24. GitHub integration (TBD)
25. Remote access (TBD)

---

## Appendix F: Dependencies Between Modules (Import Graph)

```
utils/system.py
├── core/records.py
├── core/quota_manager.py
├── core/knowledge.py
├── core/session_manager.py
└── testing/skills.py

core/records.py
├── core/knowledge.py
└── core/orchestrator.py

core/quota_manager.py
├── core/session_manager.py
└── core/orchestrator.py

core/knowledge.py
├── agents/base.py
└── core/orchestrator.py

core/session_manager.py
├── agents/base.py
└── core/orchestrator.py

agents/base.py
├── agents/phase_agents.py
├── agents/research_agent.py
└── agents/review_agent.py

agents/phase_agents.py
└── core/orchestrator.py

agents/research_agent.py
└── testing/skills.py

agents/review_agent.py
└── core/review_loop.py

core/orchestrator.py
├── core/dynamic_plan.py
├── core/user_interaction.py
├── core/review_loop.py
├── skills/__init__.py
└── hooks/*.py

skills/__init__.py
└── .claude/skills/*.yaml

hooks/*.py
└── .claude/hooks/*.yaml
```

---

## Appendix G: Critical Path Items

Items that MUST complete in sequence:

```
1. [DONE] utils/system.py
     ↓
2. [DONE] core/quota_manager.py
     ↓
3. [DONE] core/session_manager.py
     ↓
4. [DONE] agents/base.py
     ↓
5. [BLOCKING] agents/review_agent.py ← CURRENT BLOCKER
     ↓
6. [DONE] core/orchestrator.py
     ↓
7. [DONE] skills/__init__.py
     ↓
8. [PENDING] Integration tests (IT-001 to IT-007)
     ↓
9. [PENDING] Live tests in Claude Code
     ↓
10. [PENDING] Spec compliance verification
     ↓
11. [PENDING] v1.0 Release
```

---

## Appendix H: Risk Register

| ID | Risk | Probability | Impact | Mitigation | Status |
|----|------|-------------|--------|------------|--------|
| R-001 | CodeReviewAgent blocks release | HIGH | HIGH | Prioritize implementation | ACTIVE |
| R-002 | Live tests fail in Claude Code | MEDIUM | HIGH | Document manual fallback | MONITORING |
| R-003 | Quota parsing breaks with CLI update | MEDIUM | HIGH | Abstract parsing layer | MITIGATED |
| R-004 | Context compaction loses state | HIGH | MEDIUM | Recovery protocol implemented | MITIGATED |
| R-005 | Session lock file corruption | LOW | MEDIUM | Auto-cleanup after 5 minutes | MITIGATED |
| R-006 | Multi-language linters unavailable | MEDIUM | MEDIUM | Research agent fallback chain | MITIGATED |
| R-007 | Integration tests hang | MEDIUM | LOW | 5-minute timeout per test | MITIGATED |
| R-008 | Documentation incomplete at release | LOW | LOW | Document as implementing | MONITORING |

---

## Appendix I: v1.0 Release Checklist

### Pre-Release Requirements

#### Code Quality
- [ ] All 20 modules pass unit tests
- [ ] Code coverage ≥ 80% overall
- [ ] No mypy strict errors
- [ ] No ruff lint errors
- [ ] All TODO comments resolved or tracked

#### Module Completion
- [ ] utils: 6/6 checkboxes (currently 4/6)
- [ ] records-system: 6/6 checkboxes
- [ ] quota: 6/6 checkboxes (currently 4/6)
- [ ] knowledge: 6/6 checkboxes
- [ ] session: 6/6 checkboxes
- [ ] agents: 6/6 checkboxes
- [ ] research: 6/6 checkboxes
- [ ] code-review: 6/6 checkboxes (currently 2/6) **BLOCKING**
- [ ] orchestrator: 6/6 checkboxes (currently 4/6)
- [ ] dynamic-plan: 6/6 checkboxes
- [ ] user-interaction: 6/6 checkboxes
- [ ] review-loop: 6/6 checkboxes
- [ ] skills: 6/6 checkboxes (currently 4/6)
- [ ] hooks: 6/6 checkboxes
- [ ] plugin: 6/6 checkboxes
- [ ] testing: 6/6 checkboxes
- [ ] system-capabilities: 6/6 checkboxes
- [ ] notifications: 6/6 checkboxes

#### Integration Testing
- [ ] IT-001: Full Phase Workflow - PASS
- [ ] IT-002: Quota Pause and Resume - PASS
- [ ] IT-003: Session Lock Handling - PASS
- [ ] IT-004: Dynamic Plan Updates - PASS
- [ ] IT-005: Review Loop Cycles - PASS
- [ ] IT-006: Knowledge Sharing - PASS
- [ ] IT-007: Compaction Recovery - PASS

#### Live Testing
- [ ] /beyond-ralph:start works in Claude Code
- [ ] /beyond-ralph:resume works in Claude Code
- [ ] /beyond-ralph:status works in Claude Code
- [ ] /beyond-ralph:pause works in Claude Code
- [ ] Quota pausing works with real quotas
- [ ] Subagent output streams correctly
- [ ] Full Phase 1-8 workflow completes

#### Documentation
- [ ] README.md complete with quick start
- [ ] User guide in docs/user/
- [ ] Developer guide in docs/developer/
- [ ] CHANGELOG.md for v1.0
- [ ] Evidence in docs/evidence/

#### Packaging
- [ ] Clean install on Ubuntu 22.04
- [ ] Clean install on macOS 14
- [ ] All dependencies in pyproject.toml
- [ ] Entry points registered correctly
- [ ] No external tool dependencies

### Release Steps

1. Verify all checkboxes in this list
2. Create release branch: `git checkout -b release/v1.0`
3. Update version in pyproject.toml
4. Generate CHANGELOG.md
5. Run full test suite: `uv run pytest`
6. Create git tag: `git tag v1.0.0`
7. Push tag: `git push origin v1.0.0`
8. Build package: `uv build`
9. Test clean install: `uv pip install dist/*.whl`
10. Announce release
