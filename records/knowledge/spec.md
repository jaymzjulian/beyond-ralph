# Module 7: Knowledge Base - Specification

**Module**: knowledge
**Location**: `src/beyond_ralph/core/knowledge.py`
**Dependencies**: None (foundational)

## Purpose

Shared knowledge storage enabling agents to learn from each other and ask follow-up questions.

## Requirements

### R1: Knowledge Storage
- Markdown files with YAML frontmatter
- Store in beyondralph_knowledge/
- Include source session UUID
- Categorize: design, implementation, testing, issue, resolution

### R2: Knowledge Retrieval
- Search by topic/keyword
- List recent entries
- Get entries by source session (for follow-up)

### R3: Agent Integration
- Agents check knowledge BEFORE asking orchestrator
- Agents write learnings for future agents
- Enable follow-up questions to source sessions

## Entry Format

```yaml
---
uuid: abc-123-def
created_by_session: session-xyz-789
date: 2024-02-01T10:30:00Z
category: implementation
tags:
  - auth
  - jwt
---

# Topic Title

## Summary
...

## Details
...

## Questions for Source
...
```

## Interface

```python
class KnowledgeBase:
    async def write(self, entry: KnowledgeEntry) -> str
    async def read(self, uuid: str) -> KnowledgeEntry | None
    async def search(self, query: str) -> list[KnowledgeEntry]
    async def list_recent(self, hours: int = 24) -> list[KnowledgeEntry]
    async def get_by_session(self, session_id: str) -> list[KnowledgeEntry]
```

## Testing Requirements

- Test write/read cycle
- Test search functionality
- Test recency filtering
- Test session filtering
