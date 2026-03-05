# Beyond Ralph - Complete Modular Specification

**Version**: 1.0.0
**Status**: Phase 5 Complete - Ready for Implementation
**Date**: 2024-02-01
**Phase 5 Review**: No user-blocking uncertainties. All technical items to be researched autonomously.

---

## Executive Summary

Beyond Ralph is an autonomous multi-agent development system for Claude Code that implements the Spec and Interview Coder methodology. It runs as a native Claude Code plugin, spawning and coordinating specialized agents to deliver complete projects from specification to tested, documented code.

### Core Principles

1. **100% Autonomous** (after interview) - No user approval needed for technical decisions
2. **100% Test Coverage** - Strictly required, gaps documented in UNTESTABLE.md
3. **Three-Agent Trust** - Coding + Testing + Review for every implementation
4. **Dynamic Planning** - Project plan evolves as modules discover requirements
5. **Context Efficient** - Orchestrator delegates aggressively, recovers from compaction

---

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BEYOND RALPH SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   MODULE 1  │  │   MODULE 2  │  │   MODULE 3  │  │   MODULE 4  │    │
│  │    Core     │  │   Agents    │  │   Testing   │  │    Plugin   │    │
│  │ Orchestrator│  │  Framework  │  │   Skills    │  │ Integration │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐    │
│  │   MODULE 5  │  │   MODULE 6  │  │   MODULE 7  │  │   MODULE 8  │    │
│  │   Session   │  │   Quota     │  │  Knowledge  │  │   Records   │    │
│  │  Management │  │  Management │  │    Base     │  │   System    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   MODULE 9  │  │  MODULE 10  │  │  MODULE 11  │  │  MODULE 12  │    │
│  │  Research   │  │    Code     │  │   System    │  │ Notification│    │
│  │    Agent    │  │   Review    │  │ Capabilities│  │   System    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## MODULE 1: Core Orchestrator

**Location**: `src/beyond_ralph/core/orchestrator.py`
**Dependencies**: Modules 5, 6, 7, 8
**Provides**: Main control loop, phase management, agent coordination

### Responsibilities

1. **Ralph-Loop Persistence**
   - Continue until ALL tasks have 7/7 checkboxes
   - Use Stop hook for persistence
   - Only pause for quota limits or fatal errors

2. **Phase Management**
   - Phase 1: Spec Ingestion (spawn Spec Agent)
   - Phase 2: Interview (spawn Interview Agent)
   - Phase 3: Spec Creation (spawn Spec Creation Agent)
   - Phase 4: Project Planning (spawn Planning Agent)
   - Phase 5: Review & Loop (spawn Review Agent, may loop to Phase 2)
   - Phase 6: Validation (spawn Validation Agent)
   - Phase 7: Implementation (spawn Coding/Testing/Review Agents)
   - Phase 8: Testing (spawn Testing Agent, may loop to Phase 6)

3. **Context Management**
   - MINIMIZE own context usage
   - Delegate ALL work to agents
   - On compaction: re-read PROJECT_PLAN.md, specs, tasks, knowledge

4. **Dynamic Plan Updates**
   - Detect when modules add requirements
   - Schedule work to fulfill inter-module requirements
   - Track discrepancies between promised and delivered

5. **Completion Assessment**
   - Spawn assessment agent to evaluate if project complete
   - Not just "is there work" - comprehensive audit

### Interface

```python
class Orchestrator:
    async def start(self, spec_path: Path) -> None:
        """Start autonomous development from specification."""

    async def resume(self, project_id: str | None = None) -> None:
        """Resume interrupted project."""

    async def pause(self) -> None:
        """Manually pause operations."""

    async def status(self) -> ProjectStatus:
        """Get current project status."""

    async def on_compaction(self) -> None:
        """Recovery protocol after context compaction."""
```

### State Machine

```
START → SPEC_INGESTION → INTERVIEW → SPEC_CREATION → PLANNING
                ↑                                        ↓
                └──────────── REVIEW (uncertainties?) ←──┘
                                    ↓ (no uncertainties)
                              VALIDATION
                                    ↓
                             IMPLEMENTATION
                                    ↓
                               TESTING
                                    ↓ (pass)          ↓ (fail)
                              COMPLETE ←──── VALIDATION (adjust plan)
```

---

## MODULE 2: Agent Framework

**Location**: `src/beyond_ralph/agents/`
**Dependencies**: Modules 5, 7
**Provides**: Base agent class, phase-specific agents

### Agent Types

#### 2.1 Base Agent
```python
class BaseAgent:
    name: str
    description: str
    tools: list[str]
    model: str  # sonnet, opus, haiku, inherit

    async def execute(self, task: Task) -> AgentResult:
        """Execute agent's task."""

    async def read_knowledge(self, topic: str) -> Knowledge | None:
        """Read from knowledge base before asking orchestrator."""

    async def write_knowledge(self, entry: KnowledgeEntry) -> None:
        """Contribute to knowledge base."""

    async def return_with_question(self, question: str) -> None:
        """Return to caller with a question (allowed behavior)."""
```

#### 2.2 Phase Agents

| Agent | Phase | Tools | Purpose |
|-------|-------|-------|---------|
| SpecAgent | 1 | Read, Glob, WebFetch | Ingest specification |
| InterviewAgent | 2 | AskUserQuestion, Read | Deep user interview |
| SpecCreationAgent | 3 | Read, Write | Create modular spec |
| PlanningAgent | 4 | Read, Write | Create project plan |
| ReviewAgent | 5 | Read, Grep | Identify uncertainties |
| ValidationAgent | 6 | Read, Grep, Bash | Validate project plan |
| ImplementationAgent | 7 | All | TDD implementation |
| TestingAgent | 8 | Read, Bash | Run tests, provide evidence |

#### 2.3 Trust Model Agents

| Agent | Role | Cannot Do |
|-------|------|-----------|
| CodingAgent | Implements features | Validate own work |
| TestingAgent | Runs tests, provides evidence | Code features |
| CodeReviewAgent | Linting, security, best practices | Dismiss findings |

### Subagent Definition Format

```yaml
# agents/implementation.md
---
name: implementation
description: TDD implementation agent. Implements features with tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
permissionMode: bypassPermissions
skills:
  - testing-skills
  - code-review-skills
---

You are an implementation agent for Beyond Ralph.

Your responsibilities:
1. Implement features using TDD
2. Write tests BEFORE implementation
3. Ensure all tests pass
4. Do NOT validate your own work - that's TestingAgent's job
...
```

---

## MODULE 3: Testing Skills

**Location**: `src/beyond_ralph/testing/`
**Dependencies**: Module 9 (Research Agent for discovery)
**Provides**: Testing capabilities for all app types

### Bundled Testing Tools

| App Type | Tools | Purpose |
|----------|-------|---------|
| API/Backend | httpx, pytest, responses | HTTP testing, mocking |
| Web UI | playwright | Browser automation (Chromium) |
| CLI | pexpect, subprocess | Process interaction |
| Desktop GUI | pillow, pyautogui | Screenshots, automation |
| Graphics/Games | opencv-python, pillow | Frame analysis |
| Mobile | Android emulator | Emulator-based testing |

### Mock API Server

```python
class MockAPIServer:
    """Generate mock server from OpenAPI spec."""

    async def from_openapi(self, spec_path: Path) -> None:
        """Parse OpenAPI and generate mock endpoints."""

    async def start(self, port: int = 8080) -> None:
        """Start mock server."""

    async def stop(self) -> None:
        """Stop mock server."""
```

### Testing Workflow

```
1. Develop against MOCK APIs first
2. All mock tests must pass
3. Automatic transition to real APIs
4. Validate against real endpoints
5. 100% coverage required (gaps in UNTESTABLE.md)
```

---

## MODULE 4: Plugin Integration

**Location**: `.claude-plugin/`, `skills/`, `agents/`, `hooks/`
**Dependencies**: All modules
**Provides**: Claude Code plugin structure

### Plugin Structure

```
beyond-ralph/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── beyond-ralph/
│       └── SKILL.md          # Main skill definition
├── agents/
│   ├── spec-agent.md
│   ├── interview-agent.md
│   ├── implementation-agent.md
│   ├── testing-agent.md
│   └── review-agent.md
├── hooks/
│   └── hooks.json            # Event handlers
└── commands/
    ├── start.md
    ├── resume.md
    ├── status.md
    └── pause.md
```

### Plugin Manifest

```json
{
  "name": "beyond-ralph",
  "description": "True Autonomous Coding - Multi-agent orchestration",
  "version": "1.0.0",
  "author": {
    "name": "jaymzjulian"
  },
  "repository": "https://github.com/jaymzjulian/beyond-ralph",
  "homepage": "https://github.com/jaymzjulian/beyond-ralph"
}
```

### Skills

```yaml
# skills/beyond-ralph/SKILL.md
---
name: beyond-ralph
description: Autonomous multi-agent development. Use to start, resume, or manage autonomous coding projects.
---

Beyond Ralph - True Autonomous Coding

Commands:
- /beyond-ralph:start --spec <path> - Start new project
- /beyond-ralph:resume [project-id] - Resume project
- /beyond-ralph:status - Show status
- /beyond-ralph:pause - Pause operations
```

### Hooks

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python -m beyond_ralph.hooks.stop_handler"
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [{
          "type": "command",
          "command": "python -m beyond_ralph.hooks.quota_check"
        }]
      }
    ]
  }
}
```

---

## MODULE 5: Session Management

**Location**: `src/beyond_ralph/core/session_manager.py`
**Dependencies**: None (foundational)
**Provides**: Claude Code session spawning and control

### Responsibilities

1. **Spawn Sessions**
   - Start new Claude Code sessions via CLI
   - Return UUID of new session
   - Use `--dangerously-skip-permissions` by default
   - Support `safemode` config to toggle

2. **Session Communication**
   - Send requests to sessions by UUID
   - Return final human-readable result (not the work, the RESULT)
   - Follow up for more information
   - Loop until work complete

3. **Session Locking**
   - Check no other process using same UUID
   - Prevent concurrent access to same session

4. **Session Cleanup**
   - Clean up completed sessions
   - Handle orphaned sessions

### Interface

```python
class SessionManager:
    async def spawn(
        self,
        prompt: str,
        agent_type: str,
        safemode: bool = False,
    ) -> SessionInfo:
        """Spawn new session, return UUID."""

    async def send(self, session_id: str, message: str) -> str:
        """Send message, return result."""

    async def is_locked(self, session_id: str) -> bool:
        """Check if session is in use."""

    async def cleanup(self, session_id: str) -> None:
        """Clean up session."""
```

---

## MODULE 6: Quota Management

**Location**: `src/beyond_ralph/core/quota_manager.py`
**Dependencies**: None (foundational)
**Provides**: Claude usage quota monitoring and pausing

### Responsibilities

1. **Quota Detection**
   - Check `claude /usage` command
   - Parse session percentage
   - Parse weekly percentage

2. **Threshold Enforcement**
   - PAUSE at 85% (either session OR weekly)
   - Do NOT stop, just PAUSE

3. **Caching**
   - Cache quota status in file
   - 5-minute cache during normal operation
   - 10-minute check interval when paused

4. **Pre-Interaction Check**
   - Check quota BEFORE each agent spawn
   - Block spawn if over threshold

### Interface

```python
class QuotaManager:
    async def check(self, force_refresh: bool = False) -> QuotaStatus:
        """Check current quota status."""

    async def wait_for_reset(self) -> None:
        """Wait until quota resets (check every 10 min)."""

    def is_limited(self) -> bool:
        """Check if currently limited."""
```

### Quota Status

```python
@dataclass
class QuotaStatus:
    session_percent: float
    weekly_percent: float
    is_limited: bool  # True if either >= 85%
    checked_at: datetime
```

---

## MODULE 7: Knowledge Base

**Location**: `src/beyond_ralph/core/knowledge.py`
**Dependencies**: None (foundational)
**Provides**: Shared knowledge storage and retrieval

### Knowledge Entry Format

```yaml
# beyondralph_knowledge/auth-jwt-implementation.md
---
uuid: abc-123-def
created_by_session: session-xyz-789
date: 2024-02-01T10:30:00Z
category: implementation
tags:
  - auth
  - jwt
  - security
---

# JWT Authentication Implementation

## Summary
Implemented JWT-based authentication with refresh tokens.

## Details
- Access token expiry: 15 minutes
- Refresh token expiry: 7 days
- Stored in httpOnly cookies

## Questions for Source
- Why 15 minutes for access token?
- Should we support token blacklisting?
```

### Interface

```python
class KnowledgeBase:
    async def write(self, entry: KnowledgeEntry) -> str:
        """Write entry, return UUID."""

    async def read(self, uuid: str) -> KnowledgeEntry | None:
        """Read entry by UUID."""

    async def search(self, query: str) -> list[KnowledgeEntry]:
        """Search knowledge base."""

    async def list_recent(self, hours: int = 24) -> list[KnowledgeEntry]:
        """List recent entries."""

    async def get_by_session(self, session_id: str) -> list[KnowledgeEntry]:
        """Get entries created by specific session."""
```

---

## MODULE 8: Records System

**Location**: `src/beyond_ralph/core/records.py`
**Dependencies**: None (foundational)
**Provides**: Task tracking with 7 checkboxes

### Task Format

```markdown
### Task: Implement JWT Authentication

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested

**Description**: JWT-based authentication with refresh tokens.

**Implementation Agent**: session-abc-123
**Validation Agent**: session-def-456
**Evidence**: records/auth/evidence/jwt-auth/
```

### Interface

```python
class RecordsManager:
    async def create_task(self, module: str, task: Task) -> str:
        """Create task, return ID."""

    async def update_checkbox(
        self,
        module: str,
        task_id: str,
        checkbox: Checkbox,
        checked: bool,
    ) -> None:
        """Update checkbox (can uncheck if tests fail)."""

    async def get_module_tasks(self, module: str) -> list[Task]:
        """Get all tasks for module."""

    async def get_incomplete_tasks(self) -> list[Task]:
        """Get tasks without 7/7 checkboxes."""

    async def is_complete(self) -> bool:
        """Check if ALL tasks have 7/7 checkboxes."""
```

### Checkbox Enum

```python
class Checkbox(Enum):
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    MOCK_TESTED = "mock_tested"
    INTEGRATION_TESTED = "integration_tested"
    LIVE_TESTED = "live_tested"
```

---

## MODULE 9: Research Agent

**Location**: `src/beyond_ralph/agents/research_agent.py`
**Dependencies**: Module 11 (System Capabilities)
**Provides**: Autonomous tool discovery and installation

### Responsibilities

1. **Tool Discovery**
   - Web search for testing frameworks
   - Evaluate platform compatibility
   - Check maintenance status (GitHub stars, last commit)

2. **Preferred Tools**
   - Has opinions when user doesn't specify
   - Playwright for web, pytest for Python, etc.

3. **Mandatory Fallback**
   - When a tool fails, MUST find alternative
   - Never ask user what to try
   - Document failures and solutions

4. **Autonomous Installation**
   - Install without user approval (post-interview)
   - Use appropriate package manager
   - Verify installation success

### Interface

```python
class ResearchAgent:
    async def find_tool(
        self,
        need: str,
        category: ToolCategory,
    ) -> DiscoveredTool:
        """Find tool for a need."""

    async def install_tool(self, tool: DiscoveredTool) -> bool:
        """Install tool, return success."""

    async def handle_failure(
        self,
        failed_tool: str,
        error: str,
        category: ToolCategory,
    ) -> DiscoveredTool | None:
        """Find and install alternative when tool fails."""
```

---

## MODULE 10: Code Review

**Location**: `src/beyond_ralph/agents/review_agent.py`
**Dependencies**: Module 9 (for linter discovery)
**Provides**: Mandatory code review with linting, security, and semantic analysis

### Supported Languages

| Language | Linters | Security | Dependencies |
|----------|---------|----------|--------------|
| Python | ruff, mypy, bandit | bandit, detect-secrets | safety |
| JavaScript | eslint | detect-secrets | npm audit |
| TypeScript | eslint, tsc | detect-secrets | npm audit |
| Rust | clippy | cargo audit | cargo audit |
| Go | staticcheck, go vet | detect-secrets | - |
| Kotlin | detekt, ktlint | detect-secrets | - |
| C | cppcheck | detect-secrets | - |
| C++ | cppcheck, clang-tidy | detect-secrets | - |
| Ruby | rubocop, brakeman | brakeman | bundle audit |
| Java | checkstyle | detect-secrets | - |
| Swift | swiftlint | detect-secrets | - |

### Review Categories

| Category | Severity | Description |
|----------|----------|-------------|
| **INCOMPLETE** | CRITICAL/HIGH | TODOs, unimplemented!(), NotImplementedError, placeholders |
| Security | CRITICAL | OWASP, vulnerabilities, secrets |
| Dependencies | CRITICAL | Known vulnerable packages |
| Linting | MEDIUM-HIGH | Language-specific issues |
| Types | MEDIUM-HIGH | Type checking errors |
| Complexity | MEDIUM-HIGH | High cyclomatic complexity |
| Semantic | VARIES | LLM-detected issues (code doesn't do what it claims) |

### CRITICAL: Incomplete Code Detection

**Beyond Ralph NEVER accepts incomplete code.** The following patterns are flagged:

```python
# Python - CRITICAL
raise NotImplementedError()  # CRITICAL
...                          # CRITICAL (ellipsis placeholder)
# TODO: implement later      # HIGH

# Rust - CRITICAL
todo!()                      # CRITICAL
unimplemented!()             # CRITICAL
panic!("not implemented")    # CRITICAL

# Kotlin - CRITICAL
TODO()                       # CRITICAL
notImplementedError()        # CRITICAL

# JavaScript/TypeScript - CRITICAL
throw new Error("Not implemented")  # CRITICAL
// TODO: add later                  # HIGH

# C/C++ - CRITICAL
assert(false)                # CRITICAL
#error not implemented       # CRITICAL

# Ruby - CRITICAL
raise NotImplementedError    # CRITICAL
fail 'Not implemented'       # CRITICAL

# Generic - HIGH
PLACEHOLDER                  # HIGH
STUB                         # HIGH
FIXME                        # CRITICAL
XXX                          # HIGH
HACK                         # MEDIUM
```

### Review Flow

```
1. Coding Agent implements
2. Testing Agent validates
3. Code Review Agent reviews
   - FIRST: Check for incomplete code (TODOs, unimplemented, etc.)
   - Run language-specific linters
   - Run security scans
   - Check complexity
   - Check dependencies
4. ALL findings with severity MEDIUM+ must be fixed (zero tolerance)
5. Coding Agent fixes ALL items
6. Loop until Review Agent approves
```

### Interface

```python
class CodeReviewAgent:
    async def review(self) -> ReviewResult:
        """Perform full code review."""

    async def detect_languages(self) -> list[str]:
        """Detect all languages in project."""

    async def check_incomplete_code(self) -> list[ReviewItem]:
        """CRITICAL: Check for TODOs, unimplemented, placeholders."""

    async def run_linters(self, language: str) -> list[ReviewItem]:
        """Run language-specific linters."""

    async def run_security_scan(self) -> list[ReviewItem]:
        """Run security scanners."""

    async def check_dependencies(self) -> list[ReviewItem]:
        """Check for vulnerable dependencies in all languages."""
```

---

## MODULE 11: System Capabilities

**Location**: `src/beyond_ralph/utils/system.py`
**Dependencies**: None (foundational)
**Provides**: System detection and package installation

### Responsibilities

1. **Platform Detection**
   - Windows, Linux, macOS
   - WSL2 detection
   - Architecture (x86_64, ARM64)

2. **Package Manager Detection**
   - apt, dnf, pacman, brew (Linux/macOS)
   - chocolatey, winget, scoop (Windows)

3. **Passwordless Sudo Detection**
   - Check if `sudo -n true` works
   - Use liberally if available

4. **System Package Installation**
   - Browsers (Chrome, Firefox)
   - Compilers (gcc, clang)
   - Databases (PostgreSQL, Redis)
   - Display servers (Xvfb, xvnc, Wayland)

### Interface

```python
class SystemCapabilities:
    has_passwordless_sudo: bool
    package_manager: PackageManager
    platform: str
    architecture: str
    available_tools: list[str]

async def detect_capabilities() -> SystemCapabilities:
    """Detect all system capabilities."""

async def install_package(package: str) -> bool:
    """Install system package."""

async def install_browser() -> bool:
    """Install browser for web testing."""

async def setup_virtual_display() -> VirtualDisplay:
    """Set up virtual display (Wayland > xvnc > Xvfb)."""
```

---

## MODULE 12: Notification System

**Location**: `src/beyond_ralph/core/notifications.py`
**Dependencies**: None (foundational)
**Provides**: Remote notifications for unsupervised operation

### Notification Channels

| Channel | Method | Credentials |
|---------|--------|-------------|
| Slack | Webhook | Webhook URL |
| Discord | Webhook | Webhook URL |
| Email | SMTP | Host, port, user, password |
| WhatsApp | whatsmeow | API credentials |
| OS | Native notifications | None |

### Notification Triggers

- **Only when blocked/needs input** (not progress updates)
- User interview questions
- Fatal errors
- Project completion
- Quota pauses

### Interface

```python
class NotificationManager:
    async def notify(
        self,
        message: str,
        level: NotificationLevel,
        channel: str | None = None,  # None = all configured
    ) -> None:
        """Send notification."""

    async def configure_channel(
        self,
        channel: str,
        credentials: dict,
    ) -> None:
        """Configure notification channel."""
```

---

## Cross-Module Requirements

### Security

- Encrypt credentials at rest (AES)
- Never log secrets
- Use .env for user secrets
- Keyring fallback for system secrets

### Compatibility

- Python 3.11+
- Windows, Linux, macOS native support
- Major version compatibility only (1.x → 1.y works)

### Configuration

```yaml
# beyond-ralph.yaml
safemode: false
max_parallel_agents: 7
quota_threshold: 85
notification:
  channels:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK}
    - type: email
      smtp_host: smtp.gmail.com
      smtp_port: 587
logging:
  level: DEBUG
  full_transcripts: true
dashboard:
  enabled: false
  port: 8080
```

### Distribution

- PyPI package: `pip install beyond-ralph`
- Claude plugin: `/plugin install beyond-ralph`
- Both installation methods supported

---

## Implementation Order

Based on dependencies:

```
Phase 1: Foundational Modules (no dependencies)
├── Module 5: Session Management
├── Module 6: Quota Management
├── Module 7: Knowledge Base
├── Module 8: Records System
└── Module 11: System Capabilities

Phase 2: Core Infrastructure
├── Module 1: Core Orchestrator
├── Module 12: Notification System
└── Module 4: Plugin Integration (basic)

Phase 3: Agent Framework
├── Module 2: Agent Framework (base)
├── Module 9: Research Agent
└── Module 10: Code Review

Phase 4: Testing & Skills
├── Module 3: Testing Skills
└── Module 2: Phase Agents

Phase 5: Integration
├── Module 4: Plugin Integration (complete)
└── End-to-end testing

Phase 6: Documentation & Packaging
├── User documentation
├── Developer documentation
└── PyPI packaging
```

---

## Acceptance Criteria

A module is complete when:

1. ✅ All functions implemented
2. ✅ 100% test coverage (gaps in UNTESTABLE.md)
3. ✅ All security scans pass
4. ✅ All linting passes
5. ✅ Documentation complete
6. ✅ Evidence generated
7. ✅ Validated by separate agent
8. ✅ 7/7 checkboxes in records

---

*This specification is a living document. Modules may add requirements to other modules during implementation.*
