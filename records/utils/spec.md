# Module 12: Utils - Specification

> Utilities: Common helpers used across all modules (foundation layer).

---

## Overview

The Utils module provides foundational utilities used by all other modules. It has no dependencies on other Beyond Ralph modules, making it the base layer of the system.

**Key Principle**: These utilities are pure helpers with no business logic.

---

## Location

`src/beyond_ralph/utils/`

---

## Components

### 12.1 Quota Checker (`quota_checker.py`)

**Purpose**: Check Claude usage quota via CLI.

**Interface**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class QuotaStatus:
    session_percent: int
    weekly_percent: int
    is_limited: bool
    is_unknown: bool  # CRITICAL: blocks operations when True
    last_checked: datetime
    reset_time: Optional[datetime]

def check_quota() -> QuotaStatus:
    """Check Claude usage quota using pexpect.

    Runs 'claude /usage', parses output, sends escape and /quit.

    Returns:
        QuotaStatus with session and weekly percentages.

    Note:
        If parsing fails, returns is_unknown=True.
        NEVER fake results - if we can't determine quota, block operations.
    """

def parse_usage_output(output: str) -> tuple[int, int]:
    """Parse usage percentages from claude /usage output.

    Returns:
        Tuple of (session_percent, weekly_percent).

    Raises:
        ValueError: If output cannot be parsed.
    """
```

---

### 12.2 Principles (`principles.py`)

**Purpose**: Core principles that ALL agents must follow.

**Interface**:
```python
CORE_PRINCIPLES: str = """
CRITICAL PRINCIPLES - NEVER VIOLATE:
1. NEVER fake results - report failures honestly
2. Block on unknown state - don't proceed with uncertainty
3. HONEST error handling - no silent exceptions
4. EXPLICIT fallbacks - all fallbacks logged
5. TRANSPARENT operations - all actions explainable
6. VERIFIABLE success - claims backed by evidence
"""

AGENT_PRINCIPLES_PROMPT: str = """
You are an autonomous agent. You MUST follow these principles:
{CORE_PRINCIPLES}

If you cannot complete a task, say so honestly.
If you encounter an error, report it clearly.
NEVER pretend to have succeeded when you haven't.
"""

def get_agent_principles_prompt() -> str:
    """Get the principles prompt for agent initialization.

    Returns:
        Complete principles prompt string.
    """
```

---

### 12.3 UUID Generator

**Purpose**: Generate unique identifiers for sessions and tasks.

**Interface**:
```python
import uuid

def generate_session_id() -> str:
    """Generate a unique session ID.

    Format: br-{8-char-hex}
    Example: br-d35605c9
    """
    return f"br-{uuid.uuid4().hex[:8]}"

def generate_task_id() -> str:
    """Generate a unique task ID.

    Format: task-{8-char-hex}
    """
    return f"task-{uuid.uuid4().hex[:8]}"

def generate_knowledge_id() -> str:
    """Generate a unique knowledge entry ID.

    Format: kb-{8-char-hex}
    """
    return f"kb-{uuid.uuid4().hex[:8]}"
```

---

### 12.4 File Utilities

**Purpose**: Common file operations.

**Interface**:
```python
from pathlib import Path
from typing import Optional

def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if not."""

def read_yaml_frontmatter(path: Path) -> tuple[dict, str]:
    """Read YAML frontmatter and content from markdown file.

    Returns:
        Tuple of (frontmatter_dict, content_string).
    """

def write_yaml_frontmatter(path: Path, frontmatter: dict, content: str) -> None:
    """Write markdown file with YAML frontmatter."""

def atomic_write(path: Path, content: str) -> None:
    """Write file atomically (write to temp, then rename).

    Prevents partial writes on crash.
    """
```

---

### 12.5 Logging Utilities

**Purpose**: Consistent logging across modules.

**Interface**:
```python
import logging
from rich.logging import RichHandler

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for a module.

    Uses rich handler for colored output.
    """

def configure_logging(level: str = "INFO") -> None:
    """Configure logging for the entire application."""
```

---

## Dependencies

| Depends On | For |
|------------|-----|
| (none) | This is the foundation layer |

---

## Error Handling

```python
class BeyondRalphError(Exception):
    """Base exception for all Beyond Ralph errors."""

class ConfigurationError(BeyondRalphError):
    """Configuration-related errors."""

class FileOperationError(BeyondRalphError):
    """File operation errors."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | All utility functions |
| Integration tests | Cross-module usage |
| Live tests | N/A |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
