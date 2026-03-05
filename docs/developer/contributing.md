# Beyond Ralph - Contributing Guide

## Welcome!

Thank you for your interest in contributing to Beyond Ralph. This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Git
- Claude Code CLI (for integration testing)

### Clone and Install

```bash
git clone https://github.com/jaymzee/beyond-ralph.git
cd beyond-ralph
uv sync
```

### Verify Setup

```bash
# Run tests
uv run pytest tests/unit -q

# Type check
uv run mypy src

# Lint
uv run ruff check src tests
```

## Code Standards

### Type Hints

All code must have type hints:

```python
# REQUIRED
def process_task(task: AgentTask, timeout: int = 300) -> AgentResult:
    ...

# NOT ACCEPTABLE
def process_task(task, timeout=300):
    ...
```

### Docstrings

Public APIs require docstrings:

```python
def spawn_session(task: str, timeout: int = 300) -> SessionInfo:
    """Spawn a new Claude Code session.

    Args:
        task: The task description for the session.
        timeout: Maximum time in seconds before timeout.

    Returns:
        SessionInfo containing the UUID and status.

    Raises:
        SessionError: If the session fails to start.
    """
```

### Error Handling

Use specific exception types:

```python
# Define specific exceptions
class BeyondRalphError(Exception):
    """Base exception for Beyond Ralph."""

class SessionError(BeyondRalphError):
    """Session-related errors."""

# Raise with context
raise SessionError(f"Failed to spawn session: {e}")
```

### Logging

Use module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)

def process():
    logger.debug("Starting process")
    logger.info("Process complete")
    logger.warning("Unexpected state")
    logger.error("Process failed: %s", error)
```

## Testing Requirements

### Coverage

- All new code must have tests
- Minimum 80% line coverage
- Branch coverage for critical paths

### Test Structure

```python
import pytest
from beyond_ralph.core.component import Component

class TestComponent:
    """Tests for Component class."""

    def test_basic_functionality(self):
        """Component does basic thing."""
        comp = Component()
        result = comp.do_thing()
        assert result == expected

    def test_edge_case(self):
        """Component handles edge case."""
        comp = Component()
        with pytest.raises(ValueError):
            comp.do_thing(invalid_input)
```

### Running Tests

```bash
# All unit tests
uv run pytest tests/unit

# Specific module
uv run pytest tests/unit/test_orchestrator.py

# With coverage
uv run pytest tests/unit --cov=src/beyond_ralph --cov-report=html

# Integration tests (requires Claude CLI)
uv run pytest tests/integration
```

## Git Workflow

### Branch Strategy

```
main                 # Always deployable
├── develop          # Integration branch
│   ├── feat/XXX     # Feature branches
│   ├── fix/XXX      # Bug fix branches
│   └── refactor/XXX # Refactoring branches
```

### Commit Messages

Use conventional commits:

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- chore: Build/tool changes
- style: Formatting

Examples:
feat(orchestrator): add phase transition logging
fix(quota): handle network timeout in quota check
docs(readme): update installation instructions
```

### Pull Request Process

1. Create feature branch from `develop`
2. Make changes with tests
3. Ensure all checks pass:
   ```bash
   uv run ruff check src tests
   uv run ruff format src tests
   uv run mypy src
   uv run pytest tests/unit
   ```
4. Push and create PR
5. Request review
6. Address feedback
7. Merge when approved

## Code Review

### What We Look For

- **Correctness**: Does the code work?
- **Tests**: Are there adequate tests?
- **Types**: Are type hints complete?
- **Docs**: Are public APIs documented?
- **Style**: Does it follow project conventions?
- **Security**: Are there any vulnerabilities?

### Review Checklist

- [ ] Tests pass
- [ ] Type checks pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] No security issues
- [ ] Follows patterns

## Adding Features

### New Agent

1. Create agent in `src/beyond_ralph/agents/`
2. Extend appropriate base class
3. Add tests in `tests/unit/`
4. Document in `docs/developer/`
5. Update registry if needed

### New Testing Capability

1. Add to `src/beyond_ralph/testing/skills.py`
2. Add evidence generation
3. Add tests
4. Document in `docs/user/testing.md`

### New CLI Command

1. Add to `src/beyond_ralph/cli.py`
2. Register in `pyproject.toml`
3. Add tests
4. Document in `docs/user/`

## Documentation

### User Docs

- Installation guides
- Quick start
- Configuration
- Troubleshooting

Location: `docs/user/`

### Developer Docs

- Architecture
- API reference
- Contributing (this doc)

Location: `docs/developer/`

### Docstrings

- Public functions and classes
- Complex internal functions
- Non-obvious behavior

## Core Principles

When contributing, always follow these principles:

### 1. Never Fake Results

```python
# WRONG - hiding failures
except Exception:
    return AgentResult(success=True)

# RIGHT - honest reporting
except Exception as e:
    return AgentResult(success=False, errors=[str(e)])
```

### 2. Provide Evidence

```python
# WRONG - claims without proof
message="Tests passed"

# RIGHT - evidence backed
message="Tests passed",
evidence_path=Path("evidence/test-output.txt")
```

### 3. Three-Agent Trust

No agent validates its own work:
- Coding agent implements
- Testing agent validates
- Review agent checks quality

### 4. Knowledge Sharing

Use the knowledge base:
- Check before duplicating work
- Store discoveries for future sessions
- Include session IDs for traceability

## Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: GitHub Discussions
- **Slack**: #beyond-ralph channel

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors list
- Release notes

Thank you for contributing!
