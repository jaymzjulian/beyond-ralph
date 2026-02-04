# Beyond Ralph - Complete Modular Specification

> **True Autonomous Coding** - Multi-agent orchestration implementing the Spec and Interview Coder methodology.

---

## Document Info

| Field | Value |
|-------|-------|
| **Version** | 6.1 |
| **Last Updated** | 2026-02-02 |
| **Source Documents** | SPEC.md, interview-decisions.md, PROJECT_PLAN.md |
| **Status** | Complete - Implementation In Progress |
| **Total Modules** | 20 (18 core + 2 optional extensions) |
| **Test Coverage** | 94.3% (865 tests) |
| **Spec Files** | All 20 modules have individual `records/[module]/spec.md` files |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Interview Decisions Summary](#interview-decisions-summary)
3. [Architecture Overview](#architecture-overview)
4. [Module Dependency Graph](#module-dependency-graph)
5. [Module Summary Table](#module-summary-table)
6. [Module Specifications](#module-specifications)
7. [Optional Extensions](#optional-extensions)
8. [Cross-Module Interfaces](#cross-module-interfaces)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Testing Strategy](#testing-strategy)
11. [Security Requirements](#security-requirements)

---

## Executive Summary

Beyond Ralph is a fully autonomous multi-agent development system that runs **inside Claude Code** as a native plugin. It implements the Spec and Interview Coder methodology:

1. **Ingest** a specification from the user (Phase 1)
2. **Interview** the user exhaustively - the ONLY approval gate (Phase 2)
3. **Create** a modular specification with clear interfaces (Phase 3)
4. **Plan** the implementation with milestones (Phase 4)
5. **Review** for uncertainties, loop back if needed (Phase 5)
6. **Validate** the plan with a separate agent (Phase 6)
7. **Implement** using TDD with three-agent trust model (Phase 7)
8. **Test** with separate validation agents (Phase 8)
9. **Loop** until 100% complete (6/6 checkboxes on every task)

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Orchestrator-Only Coordination** | The orchestrator NEVER implements, tests, or reviews. It only coordinates. |
| **Three-Agent Trust Model** | Every implementation requires Coding -> Testing -> Review agents (all separate). |
| **No Agent Is Trusted** | Every agent is validated by another agent. |
| **Interview Is The Only Approval Gate** | After Phase 2 interview, ALL decisions are autonomous. |
| **Never Fake Results** | All agents report failures honestly; unknown states block operations. |
| **Context Preservation** | Aggressive agent delegation to prevent orchestrator context bloat. |
| **100% Test Coverage** | Required for all code (only destructive APIs exempt, documented in UNTESTABLE.md). |
| **Zero Security Tolerance** | ALL security findings are blocking. |

---

## Interview Decisions Summary

These decisions were made during Phase 2 interview and are **BINDING** for all implementations.
Full decisions are in `beyondralph_knowledge/interview-decisions.md`.

### Platform & Environment

| Decision | Choice |
|----------|--------|
| Deployment environments | ALL: WSL2, Native Linux, macOS, **Native Windows** |
| Windows package managers | Chocolatey + winget + Scoop + manual installation |
| Plugin scope | Both global (~/.claude/plugins) and project-local |
| Persistence level | Very aggressive - continue until 100% complete |

### Quota & Limits

| Decision | Choice |
|----------|--------|
| Claude tier | Detect at runtime |
| Max parallel agents | 7 (Claude Code limit) |
| Quota threshold | 85% (PAUSE, not stop) |
| Check frequency | Before each agent spawn (cached 5-min TTL) |

### Code Quality (CRITICAL)

| Decision | Choice |
|----------|--------|
| Test coverage | **100% STRICTLY REQUIRED** |
| Test gap documentation | UNTESTABLE.md with justification |
| Security findings | ALL findings blocking (zero tolerance) |
| Review loop | Same Review Agent re-reviews until 0 issues |

### Autonomous Behavior

| Decision | Choice |
|----------|--------|
| Unknown tech | Research autonomously |
| Crashes/errors | Research and fix autonomously |
| Tool failures | **MANDATORY fallback** - find alternatives |
| System installs | Do whatever it takes (sudo, manual) |

### Dynamic Project Plan

| Decision | Choice |
|----------|--------|
| Plan mutability | LIVING document - modules can update |
| Inter-module requirements | Modules can add requirements to other modules |
| User input for updates | NOT required for technical requirements |
| Failure handling | AGGRESSIVELY call out, demand fixes |
| Workarounds | FORBIDDEN - fix the source, don't work around |

### Context Management

| Decision | Choice |
|----------|--------|
| Orchestrator context | MINIMIZE - delegate aggressively to agents |
| On compaction | MUST re-read plans and definitions immediately |

---

## Architecture Overview

### System Flow

```
User -> /beyond-ralph start --spec SPEC.md
         |
         v
+---------------------------------------------------------------+
|                      ORCHESTRATOR                              |
|  +-----------------------------------------------------------+ |
|  | Phase 1: Spec Ingestion    -> SpecAgent                   | |
|  | Phase 2: Interview         -> InterviewAgent              | |
|  | Phase 3: Spec Creation     -> SpecCreationAgent           | |
|  | Phase 4: Project Planning  -> PlanningAgent               | |
|  | Phase 5: Uncertainty Review-> UncertaintyReviewAgent      | |
|  | Phase 6: Plan Validation   -> ValidationAgent             | |
|  | Phase 7: Implementation    -> THREE-AGENT MODEL           | |
|  | Phase 8: Testing/Verify    -> TestingValidationAgent      | |
|  +-----------------------------------------------------------+ |
|                              |                                 |
|                              v                                 |
|  +-----------------------------------------------------------+ |
|  |           THREE-AGENT TRUST MODEL                         | |
|  |  +----------+  +----------+  +----------+                 | |
|  |  | Coding   |->| Testing  |->| Review   |                 | |
|  |  | Agent    |  | Agent    |  | Agent    |                 | |
|  |  +----------+  +----------+  +----------+                 | |
|  |       |              |             |                      | |
|  |       +----------- LOOP UNTIL REVIEW PASSES -------------+ | |
|  +-----------------------------------------------------------+ |
+---------------------------------------------------------------+
         |
         v
    Complete Project (6/6 checkboxes on ALL tasks)
```

### Output Streaming

All subagent output streams to the main Claude Code session with prefixes:

```
[BEYOND-RALPH] Phase 2: Interview Agent starting...
[AGENT:interview-abc123] I need to ask you some questions about requirements.
[USER INPUT REQUIRED]
... user answers via AskUserQuestion ...
[AGENT:interview-abc123] Great, using OAuth2. Moving on...
[BEYOND-RALPH] Interview complete, transitioning to Phase 3...
```

---

## Module Dependency Graph

```
                           +------------------+
                           |  Utils (M17)     |  (Foundation)
                           +--------+---------+
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+---------------+         +-----------------+         +----------------+
| System        |         | Knowledge       |         | Records        |
| Capabilities  |         | Base (M9)       |         | System (M10)   |
| (M14)         |         |                 |         |                |
+-------+-------+         +--------+--------+         +-------+--------+
        |                          |                          |
        |                 +--------+--------+                 |
        |                 |                 |                 |
        v                 v                 v                 v
+---------------------------------------------------------------+
|              Quota Management (M3)                             |
+---------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------+
|              Session Management (M2)                           |
+---------------------------------------------------------------+
                                    |
                                    v
+---------------------------------------------------------------+
|              Core Orchestrator (M1)                            |
|  (Coordinates all phases and agents)                           |
+---------------------------------------------------------------+
        |                           |                           |
        v                           v                           v
+---------------+         +-----------------+         +----------------+
| Phase Agents  |         | Trust Model     |         | User           |
| (M5)          |         | Agents (M6)     |         | Interaction    |
|               |         |                 |         | (M15)          |
+---------------+         +-----------------+         +----------------+
        |
        +---------------------------+---------------------------+
        |                           |                           |
        v                           v                           v
+---------------+         +-----------------+         +----------------+
| Research      |         | Code Review     |         | Testing        |
| Agent (M7)    |         | Agent (M8)      |         | Capabilities   |
|               |         |                 |         | (M13)          |
+---------------+         +-----------------+         +----------------+
```

---

## Module Summary Table

| # | Module | Location | Impl | Tests | Spec |
|---|--------|----------|------|-------|------|
| 1 | Core Orchestrator | `src/beyond_ralph/core/orchestrator.py` | ✅ | 93% | [spec](records/orchestrator/spec.md) |
| 2 | Session Management | `src/beyond_ralph/core/session_manager.py` | ✅ | 91% | [spec](records/session/spec.md) |
| 3 | Quota Management | `src/beyond_ralph/core/quota_manager.py` | ✅ | 96% | [spec](records/quota/spec.md) |
| 4 | Dynamic Plan Manager | `src/beyond_ralph/core/dynamic_plan.py` | ✅ | ⚠️ | [spec](records/dynamic-plan/spec.md) |
| 5 | Phase Agents | `src/beyond_ralph/agents/phase_agents.py` | ✅ | 99% | [spec](records/agents/spec.md) |
| 6 | Trust Model Agents | `src/beyond_ralph/agents/phase_agents.py` | ✅ | 99% | [spec](records/agents/spec.md) |
| 7 | Research Agent | `src/beyond_ralph/agents/research_agent.py` | ✅ | 94% | [spec](records/research/spec.md) |
| 8 | Code Review Agent | `src/beyond_ralph/agents/review_agent.py` | ✅ | 94% | [spec](records/code-review/spec.md) |
| 9 | Knowledge Base | `src/beyond_ralph/core/knowledge.py` | ✅ | 98% | [spec](records/knowledge/spec.md) |
| 10 | Records System | `src/beyond_ralph/core/records.py` | ✅ | 99% | [spec](records/records-system/spec.md) |
| 11 | Skills | `src/beyond_ralph/skills/` | ✅ | 100% | [spec](records/skills/spec.md) |
| 12 | Hooks | `src/beyond_ralph/hooks/` | ✅ | 94% | [spec](records/hooks/spec.md) |
| 13 | Testing Capabilities | `src/beyond_ralph/testing/` | ✅ | 93% | [spec](records/testing/spec.md) |
| 14 | System Capabilities | `src/beyond_ralph/utils/system.py` | ✅ | 96% | [spec](records/system-capabilities/spec.md) |
| 15 | User Interaction | `src/beyond_ralph/core/user_interaction.py` | ✅ | ⚠️ | [spec](records/user-interaction/spec.md) |
| 16 | Notifications | `src/beyond_ralph/core/notifications.py` | ✅ | 99% | [spec](records/notifications/spec.md) |
| 17 | Utils (Foundation) | `src/beyond_ralph/utils/` | ✅ | 96% | [spec](records/utils/spec.md) |
| 18 | Plugin Structure | `.claude-plugin/`, `skills/`, `hooks/` | ⚠️ | ⚠️ | [spec](records/plugin/spec.md) |
| 19 | GitHub Integration | `src/beyond_ralph/integrations/github.py` | ❌ | N/A | [spec](records/github-integration/spec.md) |
| 20 | Remote Access (VNC) | `src/beyond_ralph/integrations/remote_access.py` | ❌ | N/A | [spec](records/remote-access/spec.md) |

**Legend**: ✅ Complete | ⚠️ Partial | ❌ Not Started

---

## Module Specifications

Each module has a detailed specification in `records/[module]/spec.md`. Below is a summary of each.

---

### Module 1: Core Orchestrator

**Location**: `src/beyond_ralph/core/orchestrator.py`
**Spec**: [records/orchestrator/spec.md](records/orchestrator/spec.md)
**Test Coverage**: 93%

**Purpose**: Main control loop implementing ralph-loop persistence, phase management, agent coordination, and context recovery.

**Key Requirements**:
- R1: Ralph-Loop Persistence - Continue until ALL tasks have 6/6 checkboxes
- R2: Phase Management - State machine for phases 1-8
- R3: Context Management - MINIMIZE context, delegate to agents
- R4: Dynamic Plan Updates - Detect and schedule inter-module requirements
- R5: Completion Assessment - Spawn assessment agent for comprehensive audit
- R6: Agent Coordination - Up to 7 parallel agents

**Interface**:
```python
class Orchestrator:
    async def start(self, spec_path: Path) -> None
    async def resume(self, project_id: str | None = None) -> None
    async def pause(self) -> None
    def status(self) -> ProjectStatus
    def on_compaction(self) -> None  # CRITICAL: Recovery protocol
```

---

### Module 2: Session Management

**Location**: `src/beyond_ralph/core/session_manager.py`
**Spec**: [records/session/spec.md](records/session/spec.md)
**Test Coverage**: 91%

**Purpose**: Spawn and communicate with Claude Code sessions via CLI or Task tool.

**Key Requirements**:
- Spawn sessions via CLI (`claude --print -p "prompt"`)
- Lock management to prevent concurrent access
- Output streaming with [AGENT:id] prefix
- Support `--dangerously-skip-permissions` flag (safemode toggle)

**Interface**:
```python
class SessionManager:
    def spawn(self, prompt: str, use_cli: bool = False) -> Session
    def is_locked(self, session_id: str) -> bool
    async def send(self, session_id: str, message: str) -> SessionOutput
    async def complete(self, session_id: str) -> AgentResult
```

---

### Module 3: Quota Management

**Location**: `src/beyond_ralph/core/quota_manager.py`
**Spec**: [records/quota/spec.md](records/quota/spec.md)
**Test Coverage**: 96%

**Purpose**: Detect and handle Claude usage quotas to prevent hitting limits.

**Key Requirements**:
- Check via `claude /usage` command
- Threshold at 85% (PAUSE, not stop)
- Cache with 5-minute TTL
- NEVER fake results - unknown state blocks operations

**Quota States**:
| State | Session % | Weekly % | Action |
|-------|-----------|----------|--------|
| GREEN | <85 | <85 | Normal operation |
| YELLOW | 85-95 | <85 | Slow down |
| RED | >=95 | ANY | PAUSE, wait for reset |
| UNKNOWN | ? | ? | PAUSE (safety) |

---

### Module 4: Dynamic Plan Manager

**Location**: `src/beyond_ralph/core/dynamic_plan.py`
**Spec**: [records/dynamic-plan/spec.md](records/dynamic-plan/spec.md)

**Purpose**: Track inter-module requirements and project plan evolution.

**Key Requirements**:
- Modules can add requirements to other modules (no user input needed)
- Aggressively report discrepancies - no silent workarounds
- Update PROJECT_PLAN.md automatically

**Interface**:
```python
class DynamicPlanManager:
    def add_requirement(self, from_module: str, to_module: str, spec: str) -> str
    def mark_delivered(self, requirement_id: str) -> None
    def mark_failed(self, requirement_id: str, reason: str) -> None
    def report_discrepancy(self, module: str, expected: str, actual: str, severity: str) -> str
```

---

### Module 5 & 6: Phase Agents & Trust Model

**Location**: `src/beyond_ralph/agents/phase_agents.py`
**Spec**: [records/agents/spec.md](records/agents/spec.md)
**Test Coverage**: 99%

**Phase Agents** (one per phase):
- SpecAgent (Phase 1)
- InterviewAgent (Phase 2)
- SpecCreationAgent (Phase 3)
- PlanningAgent (Phase 4)
- UncertaintyReviewAgent (Phase 5)
- ValidationAgent (Phase 6)
- ImplementationAgent (Phase 7)
- TestingValidationAgent (Phase 8)

**Trust Model Agents**:
- SpecComplianceAgent - Verifies implementation matches spec
- Three-agent flow: Coding -> Testing -> Review

---

### Module 7: Research Agent

**Location**: `src/beyond_ralph/agents/research_agent.py`
**Spec**: [records/research/spec.md](records/research/spec.md)
**Test Coverage**: 94%

**Purpose**: Autonomous tool discovery and installation.

**Key Requirements**:
- Web search for testing frameworks
- Evaluate platform compatibility
- Install without user approval (post-interview)
- **MANDATORY fallback** when tools fail

**Preferred Tools**:
| Category | Tool |
|----------|------|
| Browser automation | playwright |
| Python testing | pytest |
| API testing | httpx, respx |
| Linting | ruff |

---

### Module 8: Code Review Agent

**Location**: `src/beyond_ralph/agents/review_agent.py`
**Spec**: [records/code-review/spec.md](records/code-review/spec.md)
**Test Coverage**: 94%

**Purpose**: Multi-language linting, security scanning, mandatory fix loops.

**Review Categories**:
1. **Linting** (language-specific): ruff, mypy, eslint, clippy, etc.
2. **Security (OWASP/SAST)**: semgrep, bandit, detect-secrets
3. **Best Practices**: complexity, dead code, DRY violations

**Critical Rule**: ALL findings are blocking. Coding Agent MUST fix EVERY item.

---

### Module 9: Knowledge Base

**Location**: `src/beyond_ralph/core/knowledge.py`
**Spec**: [records/knowledge/spec.md](records/knowledge/spec.md)
**Test Coverage**: 98%

**Purpose**: Shared agent memory and session tracking.

**File Format**: Markdown with YAML frontmatter
```yaml
---
uuid: kb-a1b2c3d4
created_by_session: br-d35605c9
date: '2026-02-02T00:49:45'
category: phase-2
tags: [interview, decisions]
---
# Title
Content...
```

---

### Module 10: Records System

**Location**: `src/beyond_ralph/core/records.py`
**Spec**: [records/records-system/spec.md](records/records-system/spec.md)
**Test Coverage**: 99%

**Purpose**: 6-checkbox task tracking for implementation status.

**Checkboxes** (ALL must be checked):
1. [ ] Planned
2. [ ] Implemented
3. [ ] Mock tested
4. [ ] Integration tested
5. [ ] Live tested
6. [ ] Spec Compliant

**Critical Rule**: Testing agents CAN and SHOULD remove checkboxes when failures are found.

---

### Module 11 & 12: Skills & Hooks

**Location**: `src/beyond_ralph/skills/`, `src/beyond_ralph/hooks/`
**Spec**: [records/skills/spec.md](records/skills/spec.md), [records/hooks/spec.md](records/hooks/spec.md)
**Test Coverage**: Skills 100%, Hooks 94%

**Skills**:
- `/beyond-ralph:start --spec <path>` - Start new project
- `/beyond-ralph:resume` - Resume paused project
- `/beyond-ralph:status` - Show progress
- `/beyond-ralph:pause` - Manual pause

**Hooks**:
- Stop Hook - Keep orchestrator running until complete
- Quota Hook - Check quota before agent spawning
- Subagent Stop Hook - Handle agent completion

---

### Module 13: Testing Capabilities

**Location**: `src/beyond_ralph/testing/`
**Spec**: [records/testing/spec.md](records/testing/spec.md)
**Test Coverage**: 93%

**Bundled Capabilities**:
| App Type | Tools |
|----------|-------|
| API | httpx, pytest, responses |
| Web | playwright |
| CLI | pexpect, subprocess |
| Desktop GUI | pillow, pyautogui |
| Games | pillow, opencv-python |

---

### Module 14: System Capabilities

**Location**: `src/beyond_ralph/utils/system.py`
**Spec**: [records/system-capabilities/spec.md](records/system-capabilities/spec.md)
**Test Coverage**: 96%

**Purpose**: Detect system configuration, available tools, permissions.

**Key Principle**: If passwordless sudo available, USE IT LIBERALLY.

---

### Module 15: User Interaction

**Location**: `src/beyond_ralph/core/user_interaction.py`
**Spec**: [records/user-interaction/spec.md](records/user-interaction/spec.md)

**Purpose**: Route AskUserQuestion from subagents to main Claude Code session.

---

### Module 16: Notifications

**Location**: `src/beyond_ralph/core/notifications.py`
**Spec**: [records/notifications/spec.md](records/notifications/spec.md)
**Test Coverage**: 99%

**Purpose**: Alert users when blocked or needing input.

**Channels**: Slack, Discord, Email, WhatsApp, Webhooks, OS notifications

**Trigger**: ONLY when blocked - no progress spam.

---

### Module 17: Utils (Foundation)

**Location**: `src/beyond_ralph/utils/`
**Spec**: [records/utils/spec.md](records/utils/spec.md)
**Test Coverage**: 96%

**Purpose**: Common helpers used across all modules.

**Components**:
- Quota checker
- Core principles prompt
- UUID generators
- File utilities
- Logging utilities

---

### Module 18: Plugin Structure

**Location**: `.claude-plugin/`, `skills/`, `hooks/`, `commands/`
**Spec**: [records/plugin/spec.md](records/plugin/spec.md)

**Purpose**: Native Claude Code integration as a plugin.

---

## Optional Extensions

### Extension A: GitHub Integration

**Location**: `src/beyond_ralph/integrations/github.py`
**Spec**: [records/github-integration/spec.md](records/github-integration/spec.md)
**Status**: Not Started

**Features**: Push, PR creation, issue tracking, webhooks
**Auto-Issue**: Creates GitHub issues when blocked

---

### Extension B: Remote Access (VNC)

**Location**: `src/beyond_ralph/integrations/remote_access.py`
**Spec**: [records/remote-access/spec.md](records/remote-access/spec.md)
**Status**: Not Started

**Features**: VNC sessions with random passwords for GUI testing

---

## Cross-Module Interfaces

### Key Data Types

```python
@dataclass
class AgentResult:
    success: bool
    output: str
    evidence_path: Optional[str]
    question: Optional[str]  # Return with question instead of result
    learnings: list[str]
    artifacts: dict[str, str]
    review_items: list[ReviewItem]

@dataclass
class TaskRecord:
    task_id: str
    name: str
    module: str
    planned: bool
    implemented: bool
    mock_tested: bool
    integration_tested: bool
    live_tested: bool
    spec_compliant: bool

@dataclass
class QuotaStatus:
    session_percent: int
    weekly_percent: int
    is_limited: bool
    is_unknown: bool  # CRITICAL: blocks operations
    last_checked: datetime
```

---

## Error Handling Strategy

### Exception Hierarchy

```python
class BeyondRalphError(Exception):
    """Base exception for all Beyond Ralph errors."""

class SessionError(BeyondRalphError): ...
class QuotaError(BeyondRalphError): ...
class AgentError(BeyondRalphError): ...
class KnowledgeError(BeyondRalphError): ...
class RecordsError(BeyondRalphError): ...
class ReviewError(BeyondRalphError): ...
class TestingError(BeyondRalphError): ...
class NotificationError(BeyondRalphError): ...
```

### Error Handling Principles

1. **Never swallow exceptions** - All errors must be logged and reported
2. **Unknown state blocks** - If we can't determine state, don't proceed
3. **Explicit fallbacks** - All fallback behavior must be logged
4. **Agent errors route to orchestrator** - Orchestrator decides next action

---

## Testing Strategy

### Test Categories

| Type | Purpose | Location |
|------|---------|----------|
| Unit | Individual function testing | `tests/unit/` |
| Integration | Multi-component testing | `tests/integration/` |
| Live | Real Claude Code sessions | `tests/live/` |

### Current Test Status

- **Total Tests**: 865 (854 unit + 11 integration)
- **Coverage**: 94.3%
- **Status**: All tests passing

### 6-Checkbox Requirements

Every task MUST achieve all 6 checkboxes:
1. **Planned** - Design documented
2. **Implemented** - Code written
3. **Mock tested** - Unit tests pass
4. **Integration tested** - Integration tests pass
5. **Live tested** - Works in real Claude Code
6. **Spec Compliant** - Verified by SEPARATE agent

### Coverage Requirements

- **100% test coverage required** (interview decision)
- Destructive APIs exempt (documented in UNTESTABLE.md)
- All security findings blocking

---

## Security Requirements

### OWASP/SAST Checks

ALL implementations must pass:
- Semgrep with security rulesets
- Bandit (Python)
- detect-secrets (no hardcoded credentials)
- Dependency vulnerability audits

### Secrets Handling

- Require secrets in `.env` file
- Never commit secrets to git
- Encrypt sensitive data at rest (Fernet)

### Zero Tolerance Policy

Per interview decision: **ALL security findings are blocking**.

---

## Document References

- **Original Specification**: [SPEC.md](SPEC.md)
- **Interview Decisions**: [beyondralph_knowledge/interview-decisions.md](beyondralph_knowledge/interview-decisions.md)
- **Project Plan**: [PROJECT_PLAN.md](PROJECT_PLAN.md)
- **Project Guidelines**: [CLAUDE.md](CLAUDE.md)
- **Module Specs**: [records/[module]/spec.md](records/)
- **Task Tracking**: [records/[module]/tasks.md](records/)
- **Test Coverage**: [records/test_coverage_status.md](records/test_coverage_status.md)

---

*This document is the authoritative modular specification for Beyond Ralph. Individual module details are in `records/[module]/spec.md`.*
