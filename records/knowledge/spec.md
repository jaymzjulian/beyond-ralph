# Module 3: Knowledge - Specification

> Knowledge Base: Shared agent memory and session tracking.

---

## Overview

The Knowledge module provides a shared knowledge base where all agents can read and write information. Each entry is tagged with the UUID of the session that created it, enabling follow-up questions and cross-agent learning.

**Key Principle**: Knowledge is persistent, searchable, and attributable to source sessions.

---

## Location

`src/beyond_ralph/core/knowledge.py`

---

## Components

### 3.1 Knowledge Base (`knowledge.py`)

**Purpose**: CRUD operations for shared knowledge entries.

**Interface**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class KnowledgeEntry:
    """A knowledge base entry."""
    uuid: str
    title: str
    content: str
    category: str
    created_by_session: str
    created_at: datetime
    tags: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)

class KnowledgeBase:
    """Shared knowledge base for all agents."""

    def __init__(self, path: str = "beyondralph_knowledge/") -> None:
        """Initialize knowledge base.

        Args:
            path: Path to knowledge base directory.

        Creates directory if it doesn't exist.
        """

    def write(
        self,
        title: str,
        content: str,
        category: str,
        session_id: str,
        tags: Optional[list[str]] = None
    ) -> str:
        """Write new knowledge entry.

        Args:
            title: Entry title (used for filename slug).
            content: Markdown content.
            category: Category for organization (e.g., "phase-2", "architecture").
            session_id: UUID of session creating this entry.
            tags: Optional list of tags for searchability.

        Returns:
            UUID of created entry.

        File Format:
            ---
            uuid: kb-{8hex}
            created_by_session: br-{8hex}
            date: '2026-02-02T00:49:45'
            category: phase-2
            tags: [interview, decisions]
            ---

            # {title}

            {content}
        """

    def read(self, uuid: str) -> Optional[KnowledgeEntry]:
        """Read knowledge entry by UUID.

        Returns:
            KnowledgeEntry if found, None otherwise.
        """

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> list[KnowledgeEntry]:
        """Search knowledge base.

        Args:
            query: Search string (matches title and content).
            category: Filter by category.
            tags: Filter by tags (OR logic).

        Returns:
            List of matching entries, sorted by relevance.
        """

    def list_recent(self, hours: int = 24) -> list[KnowledgeEntry]:
        """List recent entries.

        CRITICAL: Used for compaction recovery.
        Returns entries from the last N hours.
        """

    def get_by_session(self, session_id: str) -> list[KnowledgeEntry]:
        """Get all entries created by a session.

        Used for follow-up questions to original session.
        """

    def list_by_category(self, category: str) -> list[KnowledgeEntry]:
        """List all entries in a category."""

    def update(self, uuid: str, content: str) -> None:
        """Update existing entry content.

        Preserves frontmatter, updates content only.
        """

    def delete(self, uuid: str) -> None:
        """Delete entry.

        Removes file from disk.
        """

    def get_all(self) -> list[KnowledgeEntry]:
        """Get all entries in knowledge base."""
```

---

## File Format

Knowledge entries are stored as Markdown files with YAML frontmatter:

```markdown
---
uuid: kb-a1b2c3d4
created_by_session: br-d35605c9
date: '2026-02-02T00:49:45.577305'
category: phase-2
tags:
  - interview
  - decisions
  - authentication
related_entries:
  - kb-e5f6g7h8
---

# Interview Complete

User interview phase completed. Key decisions:

## Authentication
- Use OAuth2 with JWT tokens
- Support Google and GitHub SSO
- Session timeout: 24 hours

## Database
- PostgreSQL for primary storage
- Redis for caching

## Follow-up Questions
If you have questions about these decisions, contact session br-d35605c9.
```

---

## Categories

Standard categories:
- `phase-1` - Spec ingestion findings
- `phase-2` - Interview decisions
- `phase-3` - Modular spec details
- `phase-4` - Planning decisions
- `phase-5` - Uncertainty reviews
- `phase-6` - Validation results
- `phase-7` - Implementation notes
- `phase-8` - Testing results
- `architecture` - Architecture decisions
- `tools` - Tool discovery and configuration
- `errors` - Error patterns and solutions

---

## Dependencies

| Depends On | For |
|------------|-----|
| Module 12 (Utils) | File utilities, UUID generation |

---

## Error Handling

```python
class KnowledgeError(BeyondRalphError):
    """Knowledge base errors."""

class EntryNotFoundError(KnowledgeError):
    """Entry not found."""

class InvalidEntryError(KnowledgeError):
    """Entry format is invalid."""
```

---

## Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | CRUD operations, search |
| Integration tests | Multi-agent read/write |
| Live tests | File system persistence |

---

## Checkboxes

- [x] Planned
- [x] Implemented
- [x] Mock tested
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec Compliant
