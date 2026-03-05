# Beyond Ralph - Detailed Project Plan

> **Version**: 2.0
> **Last Updated**: 2026-02-02
> **Status**: 95% Implementation Complete, Testing Phase

---

## Executive Summary

Beyond Ralph is a fully autonomous multi-agent development system for Claude Code implementing the Spec and Interview Coder methodology. This document provides the detailed implementation plan with module dependencies, milestones, testing strategies, and risk mitigation.

### Current Status Overview

| Phase | Status | Completion |
|-------|--------|------------|
| Foundation (Tier 0) | COMPLETE | 100% |
| Core Infrastructure (Tier 1) | COMPLETE | 100% |
| Agent Framework (Tier 2) | PARTIAL | 95% |
| Orchestration (Tier 3) | COMPLETE | 100% |
| Claude Code Integration (Tier 4) | COMPLETE | 100% |
| Testing & Code Review (Tier 5) | PARTIAL | 90% |
| Advanced Features (Tier 6) | PARTIAL | 50% |

**BLOCKING ITEM**: CodeReviewAgent multi-language linting implementation

---

## Table of Contents

1. [Module Dependency Graph](#1-module-dependency-graph)
2. [Implementation Order](#2-implementation-order)
3. [Phase Milestones](#3-phase-milestones)
4. [Testing Strategy](#4-testing-strategy)
5. [Risk Mitigation](#5-risk-mitigation)
6. [Module Status Tracking](#6-module-status-tracking)
7. [Critical Path to Release](#7-critical-path-to-release)

---

## 1. Module Dependency Graph

### Visual Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TIER 0: FOUNDATION                                 │
│                                                                              │
│   ┌───────────────────────┐      ┌───────────────────────┐                  │
│   │        utils          │      │    records-system     │                  │
│   │  - Platform detection │      │  - 6-checkbox tracking│                  │
│   │  - Tool inventory     │      │  - Evidence paths     │                  │
│   │  - Sudo detection     │      │  - Task CRUD          │                  │
│   └───────────┬───────────┘      └───────────┬───────────┘                  │
│               │                              │                               │
└───────────────┼──────────────────────────────┼───────────────────────────────┘
                │                              │
                ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TIER 1: CORE INFRASTRUCTURE                           │
│                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐             │
│   │    quota    │    │  knowledge  │    │       session       │             │
│   │ - 85% limit │    │ - YAML store│    │  - CLI spawning     │             │
│   │ - Caching   │    │ - Search    │    │  - UUID tracking    │             │
│   │ - br-quota  │    │ - Recovery  │    │  - Lock mechanism   │             │
│   └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘             │
│          │                  │                      │                         │
└──────────┼──────────────────┼──────────────────────┼─────────────────────────┘
           │                  │                      │
           └──────────────────┼──────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIER 2: AGENT FRAMEWORK                              │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                        agents/base.py                              │     │
│   │     BaseAgent → PhaseAgent → TrustModelAgent                       │     │
│   └───────────────────────────────┬───────────────────────────────────┘     │
│                                   │                                          │
│        ┌──────────────────────────┼──────────────────────────┐              │
│        │                          │                          │              │
│        ▼                          ▼                          ▼              │
│   ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    │
│   │phase_agents │    │   code-review (!)   │    │      research       │    │
│   │ - Phases 1-8│    │ - Multi-lang lint   │    │  - Tool discovery   │    │
│   │ - TDD flow  │    │ - OWASP security    │    │  - Installation     │    │
│   └──────┬──────┘    └──────────┬──────────┘    └──────────┬──────────┘    │
│          │                      │                          │                │
│          │                      │ (!) BLOCKING             │                │
└──────────┼──────────────────────┼──────────────────────────┼────────────────┘
           │                      │                          │
           └──────────────────────┼──────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIER 3: ORCHESTRATION                               │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                         orchestrator                               │     │
│   │  - State machine (8 phases)  - Quota-aware operation               │     │
│   │  - Agent delegation          - Compaction recovery                 │     │
│   │  - Evidence validation       - Ralph-loop persistence              │     │
│   └───────────────────────────────┬───────────────────────────────────┘     │
│                                   │                                          │
│        ┌──────────────────────────┼──────────────────────────┐              │
│        │                          │                          │              │
│        ▼                          ▼                          ▼              │
│   ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    │
│   │dynamic-plan │    │  user-interaction   │    │     review-loop     │    │
│   │ - Require.  │    │ - AskUserQuestion   │    │  - Fix cycles       │    │
│   │ - Discrepan.│    │ - Progress stream   │    │  - Mandatory fix    │    │
│   └─────────────┘    └─────────────────────┘    └─────────────────────┘    │
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TIER 4: CLAUDE CODE INTEGRATION                          │
│                                                                              │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│   │     skills      │   │      hooks      │   │        plugin           │   │
│   │  /beyond-ralph  │   │  - stop.yaml    │   │  .claude/ structure     │   │
│   │  commands       │   │  - quota-check  │   │  Entry points           │   │
│   └─────────────────┘   └─────────────────┘   └─────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TIER 5: TESTING & CODE REVIEW                          │
│                                                                              │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│   │     testing     │   │ system-capabil. │   │   code-review (full)   │   │
│   │  - TestRunner   │   │  - sudo install │   │   - BLOCKING: needs    │   │
│   │  - MockAPI      │   │  - Browser deps │   │     linter orchestra.  │   │
│   └─────────────────┘   └─────────────────┘   └─────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TIER 6: ADVANCED FEATURES                             │
│                                                                              │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│   │  notifications  │   │github-integrat. │   │    remote-access       │   │
│   │  - Slack        │   │  - PR workflows │   │  - Distributed ops     │   │
│   │  - Discord      │   │  - Issue track  │   │  - Multi-machine       │   │
│   │  - Email        │   │  (PLANNED)      │   │  (PLANNED)             │   │
│   └─────────────────┘   └─────────────────┘   └─────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dependency Matrix

| Module | Depends On | Required By |
|--------|------------|-------------|
| utils | - | ALL modules |
| records-system | - | ALL modules |
| quota | utils | session, orchestrator |
| knowledge | utils, records | agents, orchestrator |
| session | utils, quota | orchestrator |
| agents/base | knowledge, session | phase_agents, orchestrator |
| phase_agents | agents/base | orchestrator |
| code-review | agents/base | orchestrator |
| research | agents/base, knowledge | testing, orchestrator |
| orchestrator | session, quota, agents | skills, hooks |
| dynamic-plan | orchestrator, records | orchestrator |
| user-interaction | orchestrator | skills |
| review-loop | orchestrator | orchestrator |
| skills | orchestrator | plugin |
| hooks | orchestrator, quota | plugin |
| plugin | skills, hooks | end users |
| testing | utils, research | orchestrator |
| system-capabilities | utils | testing |
| notifications | orchestrator | autonomous operation |
| github-integration | orchestrator, session | PR workflows |
| remote-access | session | distributed operation |

---

## 2. Implementation Order

### Tier 0: Foundation (COMPLETE)

| Order | Module | Status | Tests | LOC |
|-------|--------|--------|-------|-----|
| 0.1 | **utils** | DONE | 34 | 852 |
| 0.2 | **records-system** | DONE | 16 | 382 |

**Exit Criteria**: Platform detection works, 6-checkbox tracking functional

### Tier 1: Core Infrastructure (COMPLETE)

| Order | Module | Status | Tests | LOC |
|-------|--------|--------|-------|-----|
| 1.1 | **quota** | DONE | 65+ | 921 |
| 1.2 | **knowledge** | DONE | 18 | 297 |
| 1.3 | **session** | DONE | 47 | 703 |

**Exit Criteria**: `br-quota` CLI works, sessions spawn via pexpect

### Tier 2: Agent Framework (95% COMPLETE)

| Order | Module | Status | Tests | LOC | Notes |
|-------|--------|--------|-------|-----|-------|
| 2.1 | **agents/base** | DONE | 22 | 539 | BaseAgent, PhaseAgent, TrustModelAgent |
| 2.2 | **phase_agents** | DONE | 30 | 753 | All 8 phases |
| 2.3 | **research** | DONE | 48 | 740 | Tool discovery |
| 2.4 | **code-review** | PARTIAL | 53 | 1059 | **BLOCKING** |

**Exit Criteria**: All agents execute, trust model enforced

**BLOCKING WORK**:
1. Complete multi-language linter orchestration
2. Finish Semgrep OWASP integration
3. Implement finding aggregation

### Tier 3: Orchestration (COMPLETE)

| Order | Module | Status | Tests | LOC |
|-------|--------|--------|-------|-----|
| 3.1 | **orchestrator** | DONE | 42 | 1083 |
| 3.2 | **dynamic-plan** | DONE | 15 | 636 |
| 3.3 | **user-interaction** | DONE | 15 | 544 |
| 3.4 | **review-loop** | DONE | 20 | 582 |

**Exit Criteria**: Full 8-phase workflow executes

### Tier 4: Claude Code Integration (COMPLETE)

| Order | Module | Status | Tests | LOC |
|-------|--------|--------|-------|-----|
| 4.1 | **skills** | DONE | 6 | 107 |
| 4.2 | **hooks** | DONE | 15 | 259 |
| 4.3 | **plugin** | DONE | N/A | YAML |

**Exit Criteria**: `/beyond-ralph start` works in Claude Code

### Tier 5: Testing & Code Review (90% COMPLETE)

| Order | Module | Status | Tests | LOC |
|-------|--------|--------|-------|-----|
| 5.1 | **testing** | DONE | 55+ | 1567 |
| 5.2 | **system-capabilities** | DONE | 20+ | (in utils) |
| 5.3 | **code-review (full)** | PARTIAL | - | - |

**Exit Criteria**: All test types work, code review produces findings

### Tier 6: Advanced Features (50% COMPLETE)

| Order | Module | Status | Tests | LOC | Priority |
|-------|--------|--------|-------|-----|----------|
| 6.1 | **notifications** | DONE | 32 | 559 | HIGH |
| 6.2 | **github-integration** | PLANNED | - | - | LOW |
| 6.3 | **remote-access** | PLANNED | - | - | LOW |

**Exit Criteria**: Notifications work, GitHub integration optional

---

## 3. Phase Milestones

### Milestone 1: Foundation Complete (ACHIEVED)

**Deliverables**:
- [x] Project structure per CLAUDE.md
- [x] Platform detection (Linux, macOS, Windows, WSL2)
- [x] Package manager detection
- [x] Tool inventory (40+ tools)
- [x] 6-checkbox task tracking system

**Evidence**: `tests/unit/test_system.py`, `tests/unit/test_records.py`

### Milestone 2: Core Infrastructure Complete (ACHIEVED)

**Deliverables**:
- [x] Quota parsing from `claude /usage`
- [x] 85% threshold detection
- [x] File-based caching (5min/10min TTL)
- [x] `br-quota` CLI command
- [x] Knowledge base with YAML frontmatter
- [x] Session spawning via pexpect
- [x] UUID tracking and lock mechanism

**Evidence**: `tests/unit/test_quota_*.py`, `tests/unit/test_knowledge.py`, `tests/unit/test_session_manager.py`

### Milestone 3: Agent Framework Complete (95% ACHIEVED)

**Deliverables**:
- [x] BaseAgent, PhaseAgent, TrustModelAgent classes
- [x] All 8 phase agents (Spec → Testing)
- [x] SpecComplianceAgent for 6th checkbox
- [x] Research agent with tool discovery
- [~] Code Review agent multi-language linting (PARTIAL)

**Remaining**:
1. Linter orchestration for JS/TS, Go, Rust, Java, C++
2. Full Semgrep OWASP integration
3. Finding aggregation across languages

**Evidence**: `tests/unit/test_phase_agents.py`, `tests/unit/test_research_agent.py`

### Milestone 4: Orchestration Complete (ACHIEVED)

**Deliverables**:
- [x] State machine with 8 phases
- [x] Quota-aware pausing
- [x] Agent delegation
- [x] Compaction recovery protocol
- [x] Ralph-loop persistence
- [x] Dynamic plan manager
- [x] User interaction routing
- [x] Review loop (mandatory fixes)

**Evidence**: `tests/unit/test_orchestrator.py`, `tests/unit/test_dynamic_plan.py`

### Milestone 5: Claude Code Integration Complete (ACHIEVED)

**Deliverables**:
- [x] `/beyond-ralph:start` command
- [x] `/beyond-ralph:resume` command
- [x] `/beyond-ralph:status` command
- [x] `/beyond-ralph:pause` command
- [x] stop.yaml hook for persistence
- [x] quota-check.yaml hook
- [x] Complete `.claude/` directory structure

**Evidence**: `tests/unit/test_skills_module.py`, `tests/unit/test_hooks.py`

### Milestone 6: Testing Framework Complete (ACHIEVED)

**Deliverables**:
- [x] TestRunner for pytest, playwright
- [x] TestingSkills for API, web, CLI, desktop GUI
- [x] MockAPIServer for development
- [x] Screenshot analysis
- [x] ClaudeDriver for live testing

**Evidence**: `tests/unit/test_testing_skills.py`, `tests/unit/test_claude_driver.py`

### Milestone 7: v1.0 Release (IN PROGRESS)

**Required for Release**:
- [ ] CodeReviewAgent multi-language linting
- [ ] All integration tests passing
- [ ] All live tests passing
- [ ] SpecComplianceAgent verification for all modules
- [ ] User documentation complete

**Target**: When blocking items resolved

---

## 4. Testing Strategy

### Test Pyramid

```
                         ╭───────────────────╮
                         │   Live Tests      │  ← Real Claude Code (5%)
                         │   tests/live/     │
                         ╰─────────┬─────────╯
                                   │
                    ╭──────────────┴──────────────╮
                    │   Integration Tests         │  ← Cross-module (15%)
                    │   tests/integration/        │
                    ╰──────────────┬──────────────╯
                                   │
             ╭─────────────────────┴─────────────────────╮
             │              Unit Tests                   │  ← Mocked (80%)
             │              tests/unit/                  │
             ╰───────────────────────────────────────────╯
```

### Test Coverage by Module

| Module | Test File | Tests | Coverage Target | Status |
|--------|-----------|-------|-----------------|--------|
| utils | test_system.py | 34 | 90% | PASS |
| records | test_records.py | 16 | 90% | PASS |
| quota | test_quota_manager.py, test_quota_checker.py | 65+ | 90% | PASS |
| knowledge | test_knowledge.py | 18 | 90% | PASS |
| session | test_session_manager.py | 47 | 90% | PASS |
| agents/base | test_agents.py | 22 | 90% | PASS |
| phase_agents | test_phase_agents.py | 30 | 90% | PASS |
| research | test_research_agent.py | 48 | 90% | PASS |
| code-review | test_review_agent.py | 53 | 90% | PARTIAL |
| orchestrator | test_orchestrator.py | 42 | 90% | PASS |
| dynamic-plan | test_dynamic_plan.py | 15 | 90% | PASS |
| user-interaction | test_user_interaction.py | 15 | 90% | PASS |
| review-loop | test_review_loop.py | 20 | 90% | PASS |
| skills | test_skills_module.py | 6 | 90% | PASS |
| hooks | test_hooks.py | 15 | 90% | PASS |
| testing | test_testing_skills.py, test_claude_driver.py | 55+ | 90% | PASS |
| notifications | test_notifications.py | 32 | 90% | PASS |

**Total Unit Tests**: 450+
**Target Coverage**: 90%

### Integration Test Plan

| Test Suite | Modules Tested | Scenarios |
|------------|----------------|-----------|
| test_workflow.py | orchestrator, agents, session | Full phase 1-8 flow |
| test_live_quota.py | quota, orchestrator | Pause/resume at 85% |
| test_live_session.py | session, hooks | Spawn, cleanup, locks |

### Live Test Plan

| Test | Description | Evidence |
|------|-------------|----------|
| Full Project Flow | `/beyond-ralph start` on sample spec | Screenshots, logs |
| Quota Handling | Verify PAUSE at 85% | Timestamps, state files |
| Review Loop | Coder fixes all review items | Cycle logs |
| Knowledge Sharing | Agents read/write knowledge | Knowledge entries |
| Trust Model | Three agents per implementation | Agent UUIDs, evidence |

### 6-Checkbox Verification Flow

```
1. Planned      → Design documented in records/[module]/spec.md
2. Implemented  → Code written, linting passes (ruff, mypy)
3. Mock Tested  → Unit tests pass with mocked dependencies
4. Integration  → Cross-module tests pass with real dependencies
5. Live Tested  → Works in real Claude Code environment
6. Spec Compliant → SpecComplianceAgent verifies implementation matches spec
```

### Test Commands

```bash
# Unit tests (fast, mocked)
uv run pytest tests/unit -v --cov=src/beyond_ralph --cov-report=html

# Integration tests (slower, real interactions)
uv run pytest tests/integration -v

# Live tests (requires Claude Code)
uv run br-live-tests

# All tests with coverage
uv run pytest tests/ -v --cov=src/beyond_ralph

# Type checking
uv run mypy src --strict

# Linting
uv run ruff check src tests
uv run ruff format --check src tests
```

---

## 5. Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Claude CLI changes** | Medium | High | Abstract CLI in session_manager.py | Switch to Task tool |
| **Quota detection fails** | Medium | High | Conservative 85% threshold; `is_unknown` blocks | Manual quota check |
| **Session spawn fails** | Low | High | Retry with exponential backoff | Fallback to Task tool |
| **Knowledge conflicts** | Low | Medium | UUID locking; file-based state | Retry with backoff |
| **Context compaction** | High | Medium | Recovery protocol; re-read key files | Checkpoint/resume |
| **Subagent timeout** | Medium | Medium | Configurable timeouts | Split into smaller tasks |

### Operational Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Long tests fail** | Medium | Medium | Checkpoint state; resume capability | Manual intervention |
| **Tool install fails** | Medium | Low | Research agent finds alternatives | Manual installation |
| **User abandons** | Low | Low | State persisted; resume anytime | N/A |
| **Rate limiting** | High | Medium | Quota-aware pausing; 10min retry | Wait for reset |

### Project Risks

| Risk | Probability | Impact | Mitigation | Contingency |
|------|-------------|--------|------------|-------------|
| **Scope creep** | Medium | Medium | Clear spec checkboxes; PR reviews | Defer to future |
| **Integration issues** | Medium | High | Modular design; explicit deps | Incremental integration |
| **Documentation drift** | High | Low | Auto-generation where possible | Documentation sprint |

### Contingency Plans

1. **If CLI breaks**: Switch to Task tool (already supported in design)
2. **If quota always unknown**: Assume 0%, warn user, don't block
3. **If session lock stuck**: 5-minute timeout, force unlock with warning
4. **If compaction occurs**: Immediately re-read PROJECT_PLAN.md, records/, knowledge/
5. **If code review tool fails**: Research agent finds alternative, log failure

---

## 6. Module Status Tracking

### Status Key

| Symbol | Meaning |
|--------|---------|
| [x] | Complete |
| [~] | Partial |
| [ ] | Not started |

### Full Module Status

| Module | Planned | Implemented | Mock | Integration | Live | Spec |
|--------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| utils | [x] | [x] | [x] | [x] | [ ] | [ ] |
| records-system | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| quota | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| knowledge | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| session | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| agents/base | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| phase_agents | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| research | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| code-review | [x] | [~] | [~] | [ ] | [ ] | [ ] |
| orchestrator | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| dynamic-plan | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| user-interaction | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| review-loop | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| skills | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| hooks | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| plugin | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| testing | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| system-capabilities | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| notifications | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| github-integration | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |
| remote-access | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Progress Summary

- **Planned**: 21/21 (100%)
- **Implemented**: 18/21 (86%) - code-review partial, github/remote not started
- **Mock Tested**: 18/21 (86%)
- **Integration Tested**: 1/21 (5%) - utils only
- **Live Tested**: 0/21 (0%)
- **Spec Compliant**: 0/21 (0%)

---

## 7. Critical Path to Release

### Blocking Items (P0)

| Item | Module | Status | Action Required |
|------|--------|--------|-----------------|
| Multi-language linting | code-review | Partial | Complete linter orchestration |
| Semgrep OWASP | code-review | Partial | Finish security integration |
| Finding aggregation | code-review | Not started | Implement cross-language aggregation |

### Release Checklist

**Phase A: Complete Blocking Items**
- [ ] CodeReviewAgent: JS/TS linting (eslint, tsc)
- [ ] CodeReviewAgent: Go linting (golint, staticcheck)
- [ ] CodeReviewAgent: Rust linting (clippy)
- [ ] CodeReviewAgent: Semgrep OWASP rules
- [ ] CodeReviewAgent: Finding aggregation

**Phase B: Integration Testing**
- [ ] Run full integration test suite
- [ ] Fix any failing tests
- [ ] Verify cross-module interactions

**Phase C: Live Testing**
- [ ] Test `/beyond-ralph start` in Claude Code
- [ ] Test quota pause/resume
- [ ] Test review loop with real code
- [ ] Test knowledge base sharing
- [ ] Collect evidence for all tests

**Phase D: Spec Compliance**
- [ ] Run SpecComplianceAgent on all modules
- [ ] Fix any spec violations
- [ ] Mark all 6th checkboxes

**Phase E: Documentation & Release**
- [ ] Complete user documentation
- [ ] Complete developer documentation
- [ ] Create release notes
- [ ] Tag v1.0.0

### Priority Queue

| Priority | Task | Module | Blocking? |
|----------|------|--------|-----------|
| P0 | Complete linter orchestration | code-review | YES |
| P0 | Integration test suite | all | YES |
| P0 | Live testing | all | YES |
| P1 | Spec compliance verification | agents | YES |
| P1 | Documentation updates | docs | NO |
| P2 | GitHub integration | github | NO |
| P2 | Remote access | remote | NO |

---

## Success Criteria

1. **Autonomous Operation**: Runs for DAYS without intervention (except interviews)
2. **Quota Awareness**: PAUSES at 85% (never stops)
3. **Three-Agent Trust**: Coding + Testing + Review for EVERY implementation
4. **6/6 Checkboxes**: ALL tasks have ALL 6 checkboxes checked
5. **Self-Contained**: Installs on clean system with `uv pip install .`
6. **Documentation**: Complete user/developer docs with process evidence
7. **Never Fake Results**: ALL agents follow honest error handling

---

*This document is the authoritative detailed project plan for Beyond Ralph.*
*Last Updated: 2026-02-02*
