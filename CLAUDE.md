# Beyond Ralph - Project Guidelines for Claude Code

> **True Autonomous Coding** - Multi-agent orchestration implementing the Spec and Interview Coder methodology.

## Project Overview

Beyond Ralph is a Claude Code plugin/skill/agent system that enables fully autonomous multi-agent development. The orchestrator spawns dedicated agents for each phase of development, from specification through implementation and testing.

**CRITICAL PRINCIPLE**: This project must be entirely self-contained. It ships everything it needs and installs its own dependencies. It CANNOT rely on external tools like SuperClaude, ralph-loop, or any other tooling that isn't explicitly bundled or installed via the project's own mechanisms.

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

Every feature MUST have all five checkboxes checked:

```markdown
- [x] Planned - design documented
- [x] Implemented - code written
- [x] Mock tested - unit tests pass
- [x] Integration tested - integration tests pass
- [x] Live tested - works in real Claude Code environment
```

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

## Agent Trust Model - CRITICAL

**NO AGENT IS TRUSTED. EVERY AGENT MUST BE VALIDATED BY ANOTHER AGENT.**

```
Coding Agent                    Validation Agent
     │                               │
     │ implements feature            │
     │                               │
     │ ─────────────────────────────>│
     │    "I completed task X"       │
     │                               │ validates implementation
     │                               │ runs independent tests
     │                               │ provides EVIDENCE
     │<─────────────────────────────│
     │   evidence document           │
     │                               │
Orchestrator validates evidence (NOT the coding agent)
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
