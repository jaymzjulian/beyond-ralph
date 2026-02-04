# Beyond Ralph - Project Guidelines for Claude Code

> **True Autonomous Coding** - Multi-agent orchestration implementing the Spec and Interview Coder methodology.

## Project Overview

Beyond Ralph is a Claude Code plugin/skill/agent system that enables fully autonomous multi-agent development. The orchestrator spawns dedicated agents for each phase of development, from specification through implementation and testing.

**CRITICAL PRINCIPLE**: This project must be entirely self-contained. It ships everything it needs and installs its own dependencies. It CANNOT rely on external tools like SuperClaude, ralph-loop, or any other tooling that isn't explicitly bundled or installed via the project's own mechanisms.

## User Experience - CRITICAL

**Beyond Ralph runs INSIDE Claude Code, not as an external tool.**

The user experience is:
1. User starts Claude Code normally
2. User types `/beyond-ralph start --spec SPEC.md`
3. Beyond Ralph orchestrator takes over, streaming ALL subagent activity into the Claude Code UI
4. User watches agents work in real-time, just like native Claude agents
5. User can intervene via AskUserQuestion prompts when agents need input
6. Progress is visible, engaging, and observable

### Streaming Subagent Output

Subagent messages MUST stream into the main Claude Code session. The approach:

```
[BEYOND-RALPH] Phase 2: Interview Agent starting...
[AGENT:interview-abc123] I need to ask you some questions about the requirements.
[AGENT:interview-abc123] 1. What authentication method do you prefer?
[USER INPUT REQUIRED]
... user answers via AskUserQuestion ...
[AGENT:interview-abc123] Great, using OAuth2. Now for testing...
[BEYOND-RALPH] Interview complete, transitioning to Phase 3...
[AGENT:planning-def456] Creating modular specification...
```

This provides:
- **Transparency**: User sees exactly what agents are doing
- **Engagement**: Watching agents work is part of the experience
- **Control**: User can observe and intervene when needed
- **Trust**: Nothing happens "behind the scenes"

## Claude Code Integration Architecture

Beyond Ralph is a **native Claude Code plugin**, not an external tool. Key integration points:

### 1. Skills (`/beyond-ralph` commands)
```
/beyond-ralph start --spec SPEC.md    # Start new project
/beyond-ralph resume                   # Resume paused project
/beyond-ralph status                   # Show progress
/beyond-ralph pause                    # Manual pause
```

### 2. Hooks (Autonomous control)
- **Stop hooks**: Keep orchestrator running until project complete
- **Pre-operation hooks**: Check quotas before agent spawning
- **Progress hooks**: Stream subagent output to UI

### 3. Agent Spawning Options

Two potential approaches for subagent management:

**Option A: Claude Code Task Tool (Preferred)**
- Use the native `Task` tool to spawn subagents
- Agents run as Claude Code subagents within the same session
- Output automatically streams to UI
- Built-in context management
- Requires investigation of Task tool capabilities

**Option B: CLI Session Spawning (Fallback)**
- Spawn `claude` CLI processes via subprocess
- Pipe stdout/stderr to main session output
- Parse and prefix output with agent identifiers
- More control but more complexity

### 4. Output Streaming Implementation

```python
# Pseudocode for streaming subagent output
async def stream_agent_output(agent_id: str, process: Process):
    """Stream subagent output to main Claude Code session."""
    async for line in process.stdout:
        # Prefix with agent identifier
        formatted = f"[AGENT:{agent_id}] {line}"
        # Output to main session (mechanism TBD based on Claude Code APIs)
        await output_to_session(formatted)
```

### 5. User Interaction Flow

```
User: /beyond-ralph start --spec myproject.md

[BEYOND-RALPH] Starting autonomous development...
[BEYOND-RALPH] Phase 1: Ingesting specification...
[AGENT:spec-001] Reading myproject.md...
[AGENT:spec-001] Identified 5 major features, 3 integration points
[AGENT:spec-001] Questions for interview phase prepared

[BEYOND-RALPH] Phase 2: Interview starting...
[AGENT:interview-002] I have questions about your requirements:

<AskUserQuestion appears in Claude Code UI>
Q: What database system should we use?
- PostgreSQL (Recommended)
- MySQL
- SQLite
- Other

User selects: PostgreSQL

[AGENT:interview-002] Noted. Next question...
... continues until interview complete ...

[BEYOND-RALPH] Phase 3: Creating specification...
... and so on ...
```

## Autonomous Testing Capabilities

Beyond Ralph ships with testing skills for various application types AND the ability to autonomously discover and install new testing tools.

### Bundled Testing Skills

| App Type | Testing Approach | Bundled Tools |
|----------|------------------|---------------|
| **API/Backend** | Mock → Real endpoints | httpx, pytest, responses |
| **Web UI** | Browser automation | playwright (cross-platform) |
| **CLI** | Process interaction | pexpect, subprocess |
| **Desktop GUI** | Screenshot analysis | pillow, pyautogui |
| **Mobile** | Emulator screenshots | appium (discovered) |
| **Games/Graphics** | Frame capture | opencv-python, pillow |

### Autonomous Tool Discovery

When Beyond Ralph encounters an app type it can't test with bundled tools:

```python
# Research Agent flow
1. Identify what kind of testing is needed
2. Search for appropriate testing frameworks
3. Evaluate options (platform support, maturity, docs)
4. Present recommendation to user via AskUserQuestion
5. If approved: install and configure automatically
6. Document in knowledge base for future projects
```

### Example: Discovering a New Testing Tool

```
[BEYOND-RALPH] Need to test: Electron desktop app on Linux
[AGENT:research-abc] Searching for Electron testing frameworks...
[AGENT:research-abc] Evaluating options:
  - Spectron: REJECTED (deprecated)
  - Playwright: SELECTED (cross-platform, actively maintained, 50k+ stars)
  - Puppeteer: Alternative (needs electron-connect wrapper)

[AGENT:research-abc] Installing playwright...
[AGENT:research-abc] Running: uv add playwright
[AGENT:research-abc] Running: playwright install
[AGENT:research-abc] Configuration added to project.
[KNOWLEDGE] Stored: electron-testing-playwright.md
```

**Note**: NO user approval requested - the spec was approved during interview phase.

### Autonomous Operation Model

**The interview phase is the ONLY approval gate.**

After interview (Phase 2) completes:
- All decisions were made during the interview
- Spec was approved by the user
- Beyond Ralph operates FULLY AUTONOMOUSLY
- No further approval requests
- Contained environment = safe to install anything

This is CRITICAL: We assume a contained/isolated environment (container, VM, etc.)
where the system can freely install packages, modify files, and run commands.

### System Package Installation

**If passwordless `sudo` is available, USE IT LIBERALLY.**

Beyond Ralph should detect and use sudo to install:
- Browsers (Chrome, Firefox, Chromium) for web testing
- Compilers (gcc, clang, make) for native extensions
- Databases (PostgreSQL, Redis, SQLite) for testing
- Runtime libraries (libssl, libffi, zlib)
- Any other tools that might be useful

**Philosophy: MORE TOOLS = BETTER.**

Don't be conservative. If something might help, install it. We're in a contained
environment - there's no risk to the host system.

```
# Example: Preparing for a web app test
sudo apt install -y google-chrome-stable  # Browser
sudo apt install -y postgresql            # Database
sudo apt install -y redis-server          # Cache
sudo apt install -y build-essential       # Compilers
```

### Tool Selection Philosophy

**Beyond Ralph chooses its preferred tools when the user hasn't specified one.**

If the user says "test my web app" without specifying a framework:
- Beyond Ralph picks Playwright (its preferred choice)
- No questions asked, just installs and uses it

If a tool doesn't work:
- **MANDATORY**: Search for and install an alternative
- Do NOT ask the user what to try next
- Do NOT give up without trying alternatives
- Document what failed and why in knowledge base

```
[AGENT:testing] Playwright failing: Chrome not available on this platform
[AGENT:testing] Searching for alternative browser automation tools...
[AGENT:testing] Found: Selenium with Firefox works on this platform
[AGENT:testing] Installing selenium and geckodriver...
[AGENT:testing] Retrying tests with Selenium...
[KNOWLEDGE] Stored: playwright-chrome-failure-arm64-linux.md
```

### Research Skill Requirements

The research skill MUST:
- Search the web for testing frameworks
- Evaluate platform compatibility
- Check if tool is actively maintained
- Read official documentation
- Compare alternatives
- **Install immediately without user approval** (post-interview)
- **Automatically find alternatives when tools fail** (MANDATORY)
- **Pick preferred tools when user hasn't specified**
- Document decisions in knowledge base

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: uv (NOT pip, NOT poetry)
- **Testing**: pytest with pytest-cov
- **Type Checking**: mypy (strict mode)
- **Linting/Formatting**: ruff
- **CLI Framework**: typer + rich

## Directory Structure

```
beyond-ralph/
├── CLAUDE.md                    # THIS FILE - Project guidelines
├── SPEC.md                      # Original specification
├── pyproject.toml               # Project configuration (uv/hatch)
├── src/beyond_ralph/
│   ├── __init__.py
│   ├── cli.py                   # CLI entry points
│   ├── core/                    # Orchestrator and session management
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Main orchestration loop
│   │   ├── session_manager.py   # Claude Code session spawning/control
│   │   └── quota_monitor.py     # Usage limit detection and pausing
│   ├── agents/                  # Agent definitions
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── spec_agent.py        # Phase 1: Spec ingestion
│   │   ├── interview_agent.py   # Phase 2: User interview
│   │   ├── planning_agent.py    # Phase 3-4: Spec creation + project planning
│   │   ├── validation_agent.py  # Phase 6: Plan validation
│   │   ├── implementation_agent.py  # Phase 7: Implementation
│   │   └── testing_agent.py     # Phase 8: Testing and verification
│   ├── skills/                  # Claude Code skills
│   │   ├── __init__.py
│   │   └── beyond_ralph.py      # Skill definitions
│   ├── hooks/                   # Claude Code hooks
│   │   ├── __init__.py
│   │   └── stop_hooks.py        # Stop hooks for autonomous operation
│   └── utils/
│       ├── __init__.py
│       ├── quota_checker.py     # Standalone quota checking script
│       ├── knowledge.py         # Knowledge base management
│       └── records.py           # Task/record keeping
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docs/
│   ├── user/                    # User documentation
│   ├── developer/               # Developer documentation
│   └── evidence/                # Process evidence
├── records/                     # Per-module task tracking
│   └── [module_name]/           # Module-specific records
└── beyondralph_knowledge/       # Shared agent knowledge base
```

## Git Usage - STRICT REQUIREMENTS

### Commit Discipline

1. **Atomic Commits**: Each commit represents ONE logical change
2. **Descriptive Messages**: Format: `<type>(<scope>): <description>`
   - Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `style`
   - Example: `feat(orchestrator): add session spawning with UUID tracking`

3. **Commit Before Major Changes**: Always commit working state before refactoring
4. **Never Commit Broken Code**: All commits must pass tests and type checks

### Branch Strategy

```
main                 # Always deployable
├── develop          # Integration branch
│   ├── feat/XXX     # Feature branches
│   ├── fix/XXX      # Bug fix branches
│   └── refactor/XXX # Refactoring branches
```

### Pre-Commit Checks (REQUIRED)

Before ANY commit:
```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src
uv run pytest tests/unit -q
```

### Git Commands Reference

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feat/session-manager

# Commit with proper message
git add -p                    # Stage interactively - review each change
git commit -m "feat(core): implement session manager with UUID tracking"

# Merge back
git checkout develop
git merge --no-ff feat/session-manager
git push origin develop

# Clean up
git branch -d feat/session-manager
```

## Code Quality Standards

### Type Hints - MANDATORY

```python
# CORRECT
def spawn_session(task: str, timeout: int = 300) -> SessionInfo:
    """Spawn a new Claude Code session."""
    ...

# WRONG - Missing types
def spawn_session(task, timeout=300):
    ...
```

### Docstrings - Required for Public APIs

```python
def spawn_session(task: str, timeout: int = 300) -> SessionInfo:
    """Spawn a new Claude Code session for a specific task.

    Args:
        task: The task description for the session.
        timeout: Maximum time in seconds before session timeout.

    Returns:
        SessionInfo containing the UUID and status of the new session.

    Raises:
        SessionSpawnError: If the session fails to start.
        QuotaExceededError: If Claude usage quota is at/near limit.
    """
```

### Error Handling

```python
# Define specific exceptions
class BeyondRalphError(Exception):
    """Base exception for Beyond Ralph."""

class SessionError(BeyondRalphError):
    """Session-related errors."""

class QuotaError(BeyondRalphError):
    """Quota/rate limit errors."""

# Use specific exception types
try:
    session = spawn_session(task)
except QuotaError:
    await pause_until_quota_reset()
except SessionError as e:
    logger.error(f"Session failed: {e}")
    raise
```

### Logging Standards

```python
import logging
from rich.logging import RichHandler

# Module-level logger
logger = logging.getLogger(__name__)

# Usage
logger.debug("Starting session spawn for task: %s", task)
logger.info("Session %s spawned successfully", session.uuid)
logger.warning("Quota at %d%%, approaching limit", quota_percent)
logger.error("Session %s failed: %s", session.uuid, error)
```

## Testing Requirements

### Test Categories and Checkboxes

Every feature MUST have all six checkboxes checked:

```markdown
- [x] Planned - design documented
- [x] Implemented - code written
- [x] Mock tested - unit tests pass
- [x] Integration tested - integration tests pass
- [x] Live tested - works in real Claude Code environment
- [x] Spec compliant - verified by SEPARATE agent that implementation matches spec
```

**Note**: The Spec Compliant checkbox is verified by a SpecComplianceAgent that is DIFFERENT from both the implementation agent and the testing agent. This catches cases where tests pass but the implementation doesn't match requirements.

### Test Structure

```python
# tests/unit/test_session_manager.py
import pytest
from beyond_ralph.core.session_manager import SessionManager

class TestSessionManager:
    """Tests for SessionManager."""

    def test_spawn_session_returns_uuid(self, mock_claude_cli):
        """Spawning a session returns a valid UUID."""
        manager = SessionManager()
        session = manager.spawn("test task")
        assert session.uuid is not None

    def test_spawn_session_respects_quota(self, mock_quota_exceeded):
        """Session spawning pauses when quota exceeded."""
        manager = SessionManager()
        with pytest.raises(QuotaError):
            manager.spawn("test task")
```

### Test-Driven Development Flow

1. Write failing test
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Commit

## Context Management - CRITICAL

**The orchestrator MUST minimize its context usage.**

### Aggressive Agent Delegation

The orchestrator should:
- **Delegate to agents aggressively** - don't do work in the orchestrator
- **Keep orchestrator context lean** - only coordination, not implementation
- **Use agents for ALL research** - don't read files directly, spawn agents
- **Use agents for ALL implementation** - orchestrator never writes code
- **Use agents for ALL testing** - orchestrator validates evidence, doesn't run tests

```
WRONG (fills orchestrator context):
[ORCHESTRATOR] Reading src/module.py...
[ORCHESTRATOR] Analyzing 500 lines of code...
[ORCHESTRATOR] Writing implementation...

CORRECT (delegates to agents):
[ORCHESTRATOR] Spawning implementation agent for module.py
[AGENT:impl-xyz] <does all the work in its own context>
[ORCHESTRATOR] Received result: "Module implemented, 3 files changed"
```

### Compaction Recovery Protocol (MANDATORY)

When the orchestrator experiences a **compaction event**, it MUST:

1. **IMMEDIATELY** re-read `PROJECT_PLAN.md`
2. **IMMEDIATELY** re-read current module specs in `records/[module]/`
3. **IMMEDIATELY** re-read task status from `records/*/tasks.md`
4. **IMMEDIATELY** check `beyondralph_knowledge/` for recent entries
5. **Resume from last known good state**

```python
async def on_compaction():
    """Recovery protocol after context compaction."""
    # Re-establish understanding
    await read_file("PROJECT_PLAN.md")
    await read_file("beyondralph_knowledge/interview-decisions.md")

    # Find current state
    current_module = await find_in_progress_module()
    await read_file(f"records/{current_module}/tasks.md")

    # Check recent knowledge
    recent_knowledge = await list_recent_knowledge(hours=24)
    for entry in recent_knowledge:
        await read_file(entry)

    # Resume
    await continue_from_last_checkpoint()
```

This prevents the orchestrator from "going off track" after losing context.

## Dynamic Project Plan - CRITICAL

**The project plan is a LIVING DOCUMENT that modules can update.**

### Modules Can Add Requirements

When a module discovers it needs something from another module:
- **Add the requirement to the project plan** (no user input needed)
- **Simple technical requirements only** (e.g., "this connection function should exist")
- **Orchestrator sees the update** and schedules the work
- **The providing module must deliver**

```
[AGENT:auth-module] I need a database connection pool from the db module.
[AGENT:auth-module] Updating PROJECT_PLAN.md: Added requirement to db module
[ORCHESTRATOR] Detected new requirement: db module must provide connection pool
[ORCHESTRATOR] Scheduling db module enhancement...
[AGENT:db-module] Implementing connection pool as requested by auth module
```

### Modules MUST Call Out Failures

When a module doesn't deliver what was promised:
- **Aggressively report the failure**
- **Demand it be fixed**
- **Update project plan with the discrepancy**
- **Do NOT silently work around it**

```
[AGENT:api-module] ERROR: db module promised get_user() but it doesn't exist!
[AGENT:api-module] Updating PROJECT_PLAN.md: db module FAILED to deliver get_user()
[AGENT:api-module] Demanding fix before I can proceed.
[ORCHESTRATOR] Detected failure: db module missing promised function
[ORCHESTRATOR] Returning to db module implementation with new requirement
[AGENT:db-module] Implementing get_user() as required by api module
```

### Dynamic Requirements Rules

1. **No user input required** - only technical requirements between modules
2. **Must be specific** - "I need function X that does Y" not "I need something"
3. **Must update PROJECT_PLAN.md** - formal record of the requirement
4. **Orchestrator mediates** - sees updates, schedules work
5. **Aggressive accountability** - call out failures, don't work around them
6. **Plan is never static** - expect it to evolve during implementation

## Agent Trust Model - CRITICAL

**NO AGENT IS TRUSTED. EVERY AGENT MUST BE VALIDATED BY ANOTHER AGENT.**

**THREE separate agents for every implementation:**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CODING AGENT   │     │ TESTING AGENT   │     │ REVIEW AGENT    │
│  (Implements)   │     │ (Validates)     │     │ (Reviews Code)  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ implements feature    │                       │
         │                       │                       │
         │──────────────────────>│                       │
         │                       │ runs tests            │
         │                       │ provides evidence     │
         │                       │                       │
         │                       │──────────────────────>│
         │                       │                       │ linting
         │                       │                       │ security scan
         │                       │                       │ best practices
         │                       │                       │ OWASP checks
         │<──────────────────────────────────────────────│
         │        review items (MUST be actioned)        │
         │                       │                       │
         │ fixes ALL items       │                       │
         │──────────────────────>│──────────────────────>│
         │                       │                       │
         └───────── REPEAT UNTIL REVIEW PASSES ─────────┘
```

### The Three Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Coding Agent** | Implements features, fixes review items | IDE, git |
| **Testing Agent** | Runs tests, validates functionality | pytest, playwright, etc. |
| **Review Agent** | Code quality, security, best practices | Linters, SAST, Semgrep |

### Review Agent Responsibilities (MANDATORY)

The Code Review Agent MUST check:

1. **Linting** (language-specific):
   - Python: ruff, mypy (strict types)
   - JavaScript/TypeScript: eslint, tsc
   - Go: golint, go vet
   - Rust: clippy
   - *Any language*: discover and use appropriate linter

2. **Security (OWASP/SAST)**:
   - Semgrep with security rulesets
   - Bandit (Python security)
   - Snyk or similar for dependencies
   - OWASP Top 10 checks
   - Secrets detection (no hardcoded keys/passwords)

3. **Best Practices**:
   - Code complexity (cyclomatic complexity)
   - DRY violations (duplicate code)
   - SOLID principles
   - Error handling patterns
   - Input validation
   - Output encoding

4. **Documentation**:
   - Public APIs have docstrings
   - Complex logic is commented
   - README updated if needed

### Coder Agent MUST Action ALL Review Items

**This is NON-NEGOTIABLE.** The Coding Agent:
- Receives review feedback
- MUST fix EVERY item flagged
- Cannot argue or dismiss items
- Must resubmit for re-review
- Loop continues until Review Agent approves

```
[AGENT:review-abc] Review complete. 7 items found:
  1. SECURITY: SQL injection risk at db.py:45
  2. SECURITY: Hardcoded API key at config.py:12
  3. LINT: Missing type hints in utils.py
  4. LINT: Unused import at main.py:3
  5. PRACTICE: Duplicate code in handlers.py:20-35 and helpers.py:10-25
  6. PRACTICE: No input validation in process_user_data()
  7. DOCS: Public function missing docstring at api.py:78

[BEYOND-RALPH] Routing to Coding Agent for fixes...

[AGENT:code-xyz] Fixing all 7 items...
[AGENT:code-xyz] Fixed: SQL injection (parameterized queries)
[AGENT:code-xyz] Fixed: Moved API key to environment variable
[AGENT:code-xyz] Fixed: Added type hints
[AGENT:code-xyz] Fixed: Removed unused import
[AGENT:code-xyz] Fixed: Extracted duplicate code to shared function
[AGENT:code-xyz] Fixed: Added input validation
[AGENT:code-xyz] Fixed: Added docstring
[AGENT:code-xyz] Resubmitting for review...

[AGENT:review-abc] Re-review complete. 0 items found. APPROVED.
```

### Evidence Requirements

```markdown
# Evidence Document: [Task Name]
- Task UUID: [uuid]
- Coding Agent UUID: [uuid]
- Validation Agent UUID: [uuid]

## Tests Executed
- [ ] Unit tests: [output/coverage]
- [ ] Integration tests: [output]
- [ ] Manual verification: [description]

## Artifacts Verified
- [ ] Code compiles/imports correctly
- [ ] No new linting errors
- [ ] Type checks pass
- [ ] Documentation updated

## Evidence Files
- Test output: evidence/[task-uuid]/test-output.txt
- Coverage report: evidence/[task-uuid]/coverage.html
- Screenshots (if applicable): evidence/[task-uuid]/screenshots/
```

## Record Keeping - MANDATORY

### Task Tracking Format

```markdown
# records/[module-name]/tasks.md

## [Module Name] Tasks

### Task: Implement Session Spawning
- [x] Planned - 2024-01-15
- [x] Implemented - 2024-01-16
- [x] Mock tested - 2024-01-16
- [ ] Integration tested
- [ ] Live tested

Notes:
- Implementation agent: [UUID]
- Validation agent: [UUID]
- Evidence: records/session-spawning/evidence/
```

### Knowledge Base Format

```markdown
# beyondralph_knowledge/[topic].md

## Topic: [Subject]
- Created by: [Session UUID]
- Date: [ISO date]

### Summary
[Brief summary of the knowledge]

### Details
[Detailed information]

### Related Topics
- [Link to related knowledge]

### Questions for Follow-up
- [Questions another agent might ask this session]
```

## Quota Management - CRITICAL

The system MUST pause when quotas are near:

```python
# Check before EVERY agent interaction
async def check_quota() -> QuotaStatus:
    """Check current Claude usage quota.

    Returns:
        QuotaStatus with session_percent and weekly_percent

    Action Required:
        If either >= 85%, pause all agent spawning
        Check every 10 minutes until reset
    """
```

### Quota States

| State | Session % | Weekly % | Action |
|-------|-----------|----------|--------|
| GREEN | <85 | <85 | Normal operation |
| YELLOW | 85-95 | <85 | Slow down, essential only |
| RED | ≥95 | ANY | PAUSE, wait for reset |
| RED | ANY | ≥85 | PAUSE, wait for reset |

## Development Workflow

### Starting Work

```bash
# 1. Activate environment
cd /home/jaymz/beyond-ralph
uv sync

# 2. Check current state
uv run pytest tests/unit -q
git status

# 3. Create feature branch
git checkout -b feat/your-feature
```

### During Development

```bash
# Run tests frequently
uv run pytest tests/unit -q

# Check types
uv run mypy src

# Format code
uv run ruff format src tests
uv run ruff check src tests --fix
```

### Completing Work

```bash
# 1. Ensure all checks pass
uv run ruff check src tests
uv run mypy src
uv run pytest

# 2. Update records
# Edit records/[module]/tasks.md

# 3. Commit with proper message
git add -p
git commit -m "feat(module): description"

# 4. Push and create PR (if applicable)
git push origin feat/your-feature
```

## Self-Containment Checklist

Before any release, verify:

- [ ] All dependencies are in pyproject.toml
- [ ] No references to external tools (SuperClaude, ralph-loop, etc.)
- [ ] Installation works on clean system: `uv pip install .`
- [ ] All skills/hooks are bundled in the package
- [ ] Documentation doesn't assume external tooling
- [ ] Tests don't require external services (use mocks)

## Common Patterns

### Spawning a Child Agent

```python
async def spawn_implementation_agent(task: Task) -> AgentResult:
    """Spawn an implementation agent for a specific task."""
    # Check quota first
    quota = await check_quota()
    if quota.is_limited:
        await pause_until_reset()

    # Check no other agent is working on this
    if await is_task_locked(task.uuid):
        raise TaskLockedError(f"Task {task.uuid} is already being worked on")

    # Spawn session
    session = await session_manager.spawn(
        prompt=task.to_prompt(),
        flags=["--dangerously-skip-permissions"] if not config.safemode else []
    )

    # Wait for completion
    result = await session.wait_for_completion()

    # Store knowledge
    await knowledge_base.store(task.uuid, result.learnings)

    return result
```

### Updating Task Status

```python
async def update_task_checkbox(
    module: str,
    task_name: str,
    checkbox: Checkbox,
    checked: bool
) -> None:
    """Update a task checkbox in the records."""
    records_path = Path(f"records/{module}/tasks.md")
    # ... implementation
```

## Anti-Patterns to Avoid

1. **Don't hardcode UUIDs** - Always generate or retrieve dynamically
2. **Don't skip validation** - Every implementation needs a separate validator
3. **Don't ignore quota limits** - Always check before spawning
4. **Don't trust agent output** - Always verify with evidence
5. **Don't commit without tests** - All code must have tests
6. **Don't use external tools** - Bundle everything needed
7. **Don't skip the interview phase** - Thorough requirements prevent rework

## Quick Reference

```bash
# Setup
uv sync                          # Install dependencies
uv run pytest                    # Run all tests
uv run mypy src                  # Type check
uv run ruff check src tests      # Lint
uv run ruff format src tests     # Format

# Development
uv run python -m beyond_ralph    # Run main CLI
uv run br-quota                  # Check quota status

# Git
git add -p                       # Stage interactively
git commit -m "type(scope): msg" # Commit with convention
git log --oneline -10            # View recent commits
```

---

*This document is the authoritative source for project guidelines. All agents MUST follow these standards.*
